"""
    flask_rl.py: simple flask rate limiter

    ***
    **uses**
    ***

    pickledb: for storing access times

    window based approach to check limits
"""
import datetime
from functools import wraps

import geocoder
import pickledb
import notifiers
import flask


class FlaskRL:
    """
    rate limiter extension for Flask that uses windows-based approach
    to limit access to routes. in the backend it uses pickleDB to store
    ip addresses & their access times. the name of this pickleDB file
    can be configured at initialization
    """

    def __init__(self, app=None, dbname="limiter.db", webhook_url=None):
        """
        initialize rate limiter

        ***
        **parameters**
        ***

        *app* : flask app
        *dbname* : name of pickle db used to store access times
        """
        self.app = app
        self.dbname = dbname
        self.cache = pickledb.load(dbname, True)
        self.date_format = "%m/%d/%Y, %H:%M:%S"
        self.webhook_url = webhook_url
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        initialize rate limiter class as a flask extension

        adds the name of the cache db into the flask app configuration
        using the config var `FRL_DB`

        ***
        **parameters**
        ***

        *app*: flask app

        ***
        """
        # add name of limiter db to the flask app config
        app.config.setdefault("FRL_DB", self.dbname)
        app.config.setdefault("WEBHOOK_URL", self.webhook_url)
        app.teardown_appcontext(self._teardown)

    def _create(self):
        """
        get pickledb instance
        """
        # return pickle db instance
        return self.cache

    def _teardown(self, exception):  # pylint: disable=unused-argument
        """
        _teardown limiter
        """
        # get app context
        ctx = flask._app_ctx_stack.top # pylint: disable=protected-access
        # if app has limiter db in context
        if hasattr(ctx, "frl_db"):
            # dump / save
            ctx.limiter_db.dump()

    def connection(self):  # pylint: disable=inconsistent-return-statements
        """
        get connection to the limiter db

        ***
        **usage**
        ***
        you can use this method to access the IP addresses & access times
        stored in pickleDB

            flask_rl = FlaskRL()

            @flask_rl.limit(limit=5, period=60)
            @app.route("/ips", methods=["GET"])
            def ips():
                cache = flask_rl.connection()
                return cache.keys() # <- will return all the IP addresses that have
                                    #    accessed the app

        once you have a list of all the ip addresses you can get the access times
        for a specific IP address using

            flask_rl = FlaskRL()

            @flask_rl.limit(limit=5, period=60)
            @app.route("/<str:ip_address>", methods=["GET"])
            def access_times(ip_address):
                cache = flask_rl.connection()
                return cache(ip_address)

        this will return a `key:value` tuple of the form `(<route_name>:<list of access_times>)`
        ***
        """
        # get app context
        ctx = flask._app_ctx_stack.top # pylint: disable=protected-access
        if ctx is not None:
            # if app doesn't have limiter db in context
            if not hasattr(ctx, "frl_db"):
                # add limiter db to context
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

    def limit(self, limit=None, period=None):
        """
        rate limiting decorator for a flask endpoint

        ***
        **parameters**
        ***

        *limit* : number of request allowed in a given period

        *period* : how often an endpoint
        ***
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
                # if ip doesn't exists in cache / store
                if not cache.exists(ip_address):
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # add access time to list
                    cache.set(ip_address, {route_name: [cur_time]})
                # if ip exists in cache / store
                else:
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # if route hasn't been accessed before
                    if not cache.dexists(ip_address, route_name):
                        # add info to cache
                        cache.dadd(ip_address, (route_name, [cur_time]))
                    # if route has been accessed before
                    else:
                        # get access times
                        access_times = cache.dget(ip_address, route_name)
                        # add current access time to old access times
                        access_times.append(cur_time)
                        # update access times in key val storage
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
