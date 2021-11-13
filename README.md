# flask_rl ![build](https://github.com/abmamo/flask_rl/workflows/build/badge.svg?branch=main)
flask rate limiting extension

## quickstart
install flask_rl
```
  pip install https://github.com/abmamo/flask_rl/archive/0.0.1.tar.gz
```
initialize `flask` app with limiter
```
  from flask import Flask
  from flask_rl import Limiter

  app = Flask(__name__)
  limiter = Limiter(app)
  # or if you are following the application factory pattern
  # limiter = Limiter()
  # limiter.init_app(app)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```
The above will limit calls to the endpoint to no more than 5 requests in a 60 second window and will return a 429 response.

## details

`flask_rl` uses `pickleDB` for storage. you can specify the filename used for the rate limiter db as
```
  from flask import Flask
  from flask_rl import Limiter

  app = Flask(__name__)
  limiter = Limiter(app, dbname=<abs or rel path to db>)
  # or
  # limiter.init_app(app, dbname=<abs or rel path to db>)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```

in addition, `flask_rl` supports sending `Slask` notifications about offending IP addresses. you just need to supply a valid `Slack` webhook URL

```
  from flask import Flask
  from flask_rl import Limiter

  app = Flask(__name__)
  limiter = Limiter(app, webhook_url=<slack webhook url>)
  # or
  # limiter.init_app(app, webhook_url=<slack webhook url>)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```
