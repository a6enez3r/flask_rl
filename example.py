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