# key / val store
import pickledb
# date / time
import datetime
# decorators
from functools import wraps
# flask apps
from flask import current_app, _app_ctx_stack, request, abort

class Limiter(object):
    """
        rate limiter class for Flask
    """
    def __init__(self, app=None, dbname="limiter.db"):
        """
            initialize rate limiter

            params:
                - app: flask WSGI instance
                - dbname: name of db used to store access times
        """
        # flask app
        self.app = app
        # name of db
        self.dbname = dbname
        # initialize pickledb cache
        self.cache = pickledb.load(dbname, True)
        # string date format
        self.date_format = "%m/%d/%Y, %H:%M:%S"
        # if flask WSGI instance found
        if app is not None:
            # init limiter with that instance
            self.init_app(app)
        
    def init_app(self, app):
        """
            initialize limiter extension with flask

            params:
                - app: flask WSGI instance
        """
        # add name of limiter db to app config
        app.config.setdefault("LIMITER_DATABASE", self.dbname)
        # pass the extension teardown method to the app
        app.teardown_appcontext(self.teardown)
    
    def create(self):
        """
            get pickledb instance
        """
        # return pickle db instance
        return self.cache
    
    def teardown(self, exception):
        """
            teardown limiter
        """
        # get app context
        ctx = _app_ctx_stack.top
        # if app has limiter db in context
        if hasattr(ctx, "limiter_db"):
            # dump / save
            ctx.limiter_db.dump()
    
    def connection(self):
        """
            get connection to the limiter db
        """
        # get app context
        ctx = _app_ctx_stack.top
        # if app context found
        if ctx is not None:
            # if app doesn't have limiter db in context
            if not hasattr(ctx, "limiter_db"):
                # add limiter db to context
                ctx.limiter_db = self.create()
            # return limiter db
            return ctx.limiter_db
    

    def check_limit_reached(self, str_access_times, limit, period):
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
        access_times = [datetime.datetime.strptime(str_access_time, self.date_format) for str_access_time in str_access_times_copy]
        # get window time
        current_window = datetime.datetime.now() - datetime.timedelta(seconds=period)
        # get num of requests in the current allowed window
        num_requests = [access_time for access_time in access_times if access_time > current_window]
        # return status
        return len(num_requests) > limit

    def limit(self, limit=None, period=None):
        """
            rate limiting decorator functions

            params:
                - limit: number of requests allowed
                - period: checking time window (in seconds)
        """
        def decorator(f):
            @wraps(f)
            def limiter_function(*args, **kwargs):
                # get IP from request
                ip_address = request.remote_addr
                # get route name from request
                route_name = str(request.url_rule).replace("/", "")
                # get cache / store
                cache = self.connection()
                # if ip doesn't exists in cache / store
                if not cache.exists(ip_address):
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # add access time to list
                    cache.set(
                        ip_address,
                        {
                            route_name: [cur_time]
                        }
                    )
                # if ip exists in cache / store
                else:
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # if route hasn't been accessed before
                    if not cache.dexists(ip_address, route_name):
                        # add info to cache
                        cache.dadd(
                            ip_address,
                            (
                                route_name, [cur_time]
                            )
                        )
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
                    limit_reached = self.check_limit_reached(str_access_times, limit, period)
                    # if limit exceeded
                    if limit_reached:
                        # abort with too many requests
                        abort(429)
                return f(*args, **kwargs)
            return limiter_function
        return decorator
