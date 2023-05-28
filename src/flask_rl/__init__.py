"""
flask_rl.py: simple flask rate limiter

The rate limiter module allows you to set custom rate limits for different routes or endpoints in
your Flask application, helping you manage and control the incoming traffic to your APIs.

Dependencies
------------

    pickledb: for storing access times & leveraging a window based approach to check rate limits
"""
import datetime
from functools import wraps
from typing import Optional

import flask
import geocoder
import notifiers
import pickledb

from flask_rl import _version

__version__ = _version.get_versions()["version"]


class FlaskRL:
    """
    Rate limiter extension for Flask that uses a window-based approach
    to limit access to routes. It utilizes pickleDB to store IP addresses
    and their access times. The name of the pickleDB file can be configured
    during initialization.
    """

    def __init__(
        self,
        app: flask.Flask = None,
        dbname: str = "limiter.db",
        webhook_url: Optional[str] = None,
    ):
        """
        Initialize the rate limiter.

        Args
        ----

            - app (Flask): flask.Flask application object.
            - dbname (str): Name of the pickleDB file used to store access times.
            - webhook_url (Optional[str]): Optional webhook URL for rate limit exceeded
                                           notifications.
        """
        self.app = app
        self.dbname = dbname
        self.cache = pickledb.load(dbname, True)
        self.date_format = "%m/%d/%Y, %H:%M:%S"
        self.webhook_url = webhook_url
        if app is not None:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        """
        Initialize the rate limiter class as a Flask extension.

        Adds the name of the cache DB to the Flask app configuration
        using the config variable `FRL_DB`.

        Args
        ----
            - app (Flask): flask.Flask application object.
        """
        # add name of limiter db to the flask app config
        app.config.setdefault("FRL_DB", self.dbname)
        app.config.setdefault("WEBHOOK_URL", self.webhook_url)
        app.teardown_appcontext(self._teardown)

    def _create(self):
        """
        Get the PickleDB instance.
        """
        return self.cache

    def _teardown(self, exception):  # pylint: disable=unused-argument
        """
        Check if limiter is configured in the current application context &
        tear it down
        """
        ctx = flask._app_ctx_stack.top  # pylint: disable=protected-access
        # if app has limiter db in context dump / save any current info in memory
        if hasattr(ctx, "frl_db"):
            ctx.limiter_db.dump()

    def connection(self):  # pylint: disable=inconsistent-return-statements
        """
        Get the connection to the limiter DB.

        This method can be used to access the IP addresses and access times
        stored in the PickleDB.

        Usage:
        - You can use this method to retrieve all the IP addresses that have
        accessed the application:

            flask_rl = FlaskRL()

            @flask_rl.limit(limit=5, period=60)
            @app.route("/ips", methods=["GET"])
            def ips():
                cache = flask_rl.connection()
                return cache.keys()

        - Once you have a list of all the IP addresses, you can get the access times
        for a specific IP address:

            flask_rl = FlaskRL()

            @flask_rl.limit(limit=5, period=60)
            @app.route("/<str:ip_address>", methods=["GET"])
            def access_times(ip_address):
                cache = flask_rl.connection()
                return cache(ip_address)

        This will return a `key:value` tuple of the form `(<route_name>:<list of access_times>)`.

        :return: Connection to the limiter DB.
        """
        ctx = flask._app_ctx_stack.top  # pylint: disable=protected-access
        if ctx is not None:
            # if app doesn't have limiter db in context inject limiter db to config / context
            if not hasattr(ctx, "frl_db"):
                ctx.limiter_db = self._create()
            return ctx.limiter_db

    def _peaked(self, str_access_times, limit, period):
        """
        check if a given set of access times exceed the
        specified limit within a given period

        params:
            - str_access_times: access times for a given endpoint
                                from a single IP address
            - limit: number of requests allowed
            - period: checking time window (in seconds)
        """
        # copy access times
        str_access_times_copy = str_access_times.copy()
        # convert to date time
        access_times = [
            datetime.datetime.strptime(str_access_time, self.date_format)
            for str_access_time in str_access_times_copy
        ]
        # get current window time
        current_window = datetime.datetime.now() - datetime.timedelta(seconds=period)
        # get num of requests in the current allowed window
        num_requests = [
            access_time for access_time in access_times if access_time > current_window
        ]
        return len(num_requests) > limit

    def limit(self, limit: Optional[int] = None, period: Optional[int] = None):
        """
        Decorator for rate limiting a Flask endpoint.

        Usage
        -----
            Apply this decorator to a Flask route to enforce rate limits on that route.

        Parameters
        ----------
            - limit (Optional[int]): The number of requests allowed in a given period.
            - period (Optional[int]): The time period in seconds during which the limit applies.

        Returns
        -------
            The decorated function.

        Example
        -------
            flask_rl = FlaskRL()

            @flask_rl.limit(limit=5, period=60)
            @app.route("/protected", methods=["GET"])
            def protected_route():
                return "This is a protected route."

        The `limit` decorator can be applied to a Flask route to enforce rate limits on that route.
        It checks the number of requests made by the client IP address within the specified period.
        If the limit is reached, it sends a rate limit warning notification (if configured) and
        returns a 429 Too Many Requests HTTP response.

        The `limit` decorator takes two optional arguments: `limit` and `period`.
        - `limit` specifies the maximum number of requests allowed within the given period.
        - `period` specifies the time duration in seconds during which the limit applies.

        The decorator function wraps the original Flask route function.
        Within the wrapper function, it retrieves the client's IP address, the route name,
        and the limiter cache/connection. It checks whether the IP address exists in the cache,
        and if not, it adds the IP address with the current access time to the cache.
        If the IP address already exists in the cache, it updates the access time for the route.
        Then, it retrieves the access times for the route and checks if the limit has been reached.
        If the limit is exceeded, it sends a rate limit warning notification (if configured)
        and returns a 429 Too Many Requests HTTP response. Otherwise, it calls the original route
        function.

        The rate limiting functionality is applied to the decorated Flask route.

        Note: This decorator requires the `connection` method to be implemented and available in
        the `FlaskRL` class.
        """

        def decorator(func):
            @wraps(func)
            def limiter_function(*args, **kwargs):
                # get IP from request
                ip_address = str(flask.request.remote_addr)
                geoloc = geocoder.ip(ip_address)
                # get route name from request
                route_name = str(flask.request.url_rule)
                # get cache / store
                cache = self.connection()
                # if ip doesn't exists in cache / store add to cache with access time
                if not cache.exists(ip_address):
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    cache.set(ip_address, {route_name: [cur_time]})
                # if ip exists in cache / store get current time and update the cache
                else:
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # if route hasn't been accessed before
                    if not cache.dexists(ip_address, route_name):
                        cache.dadd(ip_address, (route_name, [cur_time]))
                    # if route has been accessed before
                    else:
                        access_times = cache.dget(ip_address, route_name)
                        access_times.append(cur_time)
                        cache.drem(ip_address)
                        cache.dcreate(ip_address)
                        cache.dadd(ip_address, (route_name, access_times))
                    # get access times
                    str_access_times = cache.dget(ip_address, route_name)
                    # convert access times to datetime
                    limit_reached = self._peaked(str_access_times, limit, period)
                    # if limit exceeded
                    if limit_reached:
                        with self.app.app_context():
                            if self.webhook_url is not None:
                                slack = notifiers.get_notifier("slack")
                                message = f"""
                                    flask_rl: excess rate limit warning

                                    ip: {ip_address}

                                    route: {str(flask.request.url_rule)}

                                    country: {geoloc.country}

                                    city: {geoloc.city}
                                """
                                slack.notify(
                                    webhook_url=self.webhook_url, message=message
                                )
                        # flask.abort with too many requests
                        flask.abort(429)
                return func(*args, **kwargs)

            return limiter_function

        return decorator
