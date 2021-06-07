# flask_rl ![build](https://github.com/abmamo/flask_rl/workflows/build/badge.svg?branch=main)
flask rate limiting extension

## quickstart
install flask_rl
```
  pip3 install https://github.com/abmamo/flask_rl/archive/v0.0.1.tar.gz
```
you can use the rate limiter as
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
will limit calls to the endpoint to no more than 5 requests in a 60 second window and will return a 429 response
