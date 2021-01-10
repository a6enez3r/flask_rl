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
  lm = Limiter(app)
  # or
  # lm = Limiter()
  # lm.init_app(app)

  @app.route("/")
  @lm.limit(limit=5, period=60)
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```
will limit calls to the endpoint to 5 in the past 60 seconds and will return a 429 response
