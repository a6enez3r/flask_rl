import pickledb
import datetime
from functools import wraps
from flask import current_app, _app_ctx_stack, request, abort

class Limiter(object):
    def __init__(self, app=None, dbname="limiter.db"):
        self.app = app
        self.dbname = dbname
        self.cache = pickledb.load(dbname, True)
        self.date_format = "%m/%d/%Y, %H:%M:%S"
        if app is not None:
            self.init_app(app)
        
    def init_app(self, app):
        app.config.setdefault("LIMITER_DATABASE", self.dbname)
        app.teardown_appcontext(self.teardown)
    
    def create(self):
        return self.cache
    
    def teardown(self, exception):
        ctx = _app_ctx_stack.top
        if hasattr(ctx, "limiter_db"):
            ctx.limiter_db.dump()
    
    def connection(self):
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "limiter_db"):
                ctx.limiter_db = self.create()
            return ctx.limiter_db
    

    def check_limit_reached(self, str_access_times, limit, period):
        # copy access times
        str_access_times_copy = str_access_times.copy()
        # convert to date time
        access_times = [datetime.datetime.strptime(str_access_time, self.date_format) for str_access_time in str_access_times_copy]
        # get window time
        current_window = datetime.datetime.now() - datetime.timedelta(seconds=period)
        # check if access times have been
        num_requests = [access_time for access_time in access_times if access_time > current_window]
        # return status
        return len(num_requests) > limit

    def limit(self, limit=None, period=None):
        def decorator(f):
            @wraps(f)
            def limiter_function(*args, **kwargs):
                # get IP from request
                ip_address = request.remote_addr
                # get cache / store
                cache = self.connection()
                # if ip doesn't exists
                if not cache.exists(ip_address):
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # add access time to list
                    cache.set(ip_address, [cur_time])
                # if ip exists
                else:
                    # get current time
                    cur_time = datetime.datetime.now().strftime(self.date_format)
                    # add access time to lists
                    cache.ladd(ip_address, cur_time)
                    # get access times
                    str_access_times = cache.get(ip_address)
                    # convert access times to datetime
                    limit_reached = self.check_limit_reached(str_access_times, limit, period)
                    # if limit exceeded
                    if limit_reached:
                        # abort with too many requests
                        abort(429)
                return f(*args, **kwargs)
            return limiter_function
        return decorator
