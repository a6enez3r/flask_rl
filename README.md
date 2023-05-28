# `flask_rl` [![pipeline](https://github.com/a6enez3r/flask_rl/actions/workflows/pipeline.yml/badge.svg)](https://github.com/a6enez3r/flask_rl/actions/workflows/pipeline.yml)

window based flask rate limiting extension

## `install`

`flask_rl` can be installed from source :-

```shell
  git clone https://github.com/a6enez3r/flask_rl
  cd flask_rl
```

- Create a virtual environment & install all dependencies

```shell
  python3 -m venv venv
  source venv/bin/activate
  make deps
```
- Install the CLI itself

```shell
  make pkg-install
```

## `quickstart`

initialize `flask` app with limiter
```python
  from flask import Flask
  from flask_rl import FlaskRL

  app = Flask(__name__)
  limiter = FlaskRL(app)
  # or if you are following the application factory pattern
  # limiter = FlaskRL()
  # limiter.init_app(app)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```
The above will limit calls to the endpoint to no more than 5 requests in a 60 second window and will return a 429 response. To see
this you can run the `example.py` app and refresh your browser *6* times to ensure a `429 Too Many Requests` error gets raised :-

```shell
  python3 example.py
```

`flask_rl` uses `pickleDB` for storage. you can specify the filename used for the rate limiter db as

```python
  from flask import Flask
  from flask_rl import FlaskRL

  app = Flask(__name__)
  limiter = FlaskRL(app, dbname=<abs or rel path to db>)
  # or
  # limiter.init_app(app, dbname=<abs or rel path to db>)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```

in addition, `flask_rl` supports sending `Slack` notifications about offending IP addresses. you just need to supply a valid `Slack` webhook URL

```python
  from flask import Flask
  from flask_rl import FlaskRL

  app = Flask(__name__)
  limiter = FlaskRL(app, webhook_url=<slack webhook url>)
  # or
  # limiter.init_app(app, webhook_url=<slack webhook url>)
  @app.route("/")
  @limiter.limit(limit=5, period=60) # limit to 5 requests / minute
  def home():
      return "Home"

  if __name__ == "__main__":
      app.run()
```
