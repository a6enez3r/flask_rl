"""
    conftest.py: contains pytest fixtures
"""
# sys
import os

# testing
import pytest

# flask
from flask import Flask

# flask_rl extension class
from flask_rl import FlaskRL

# test limit for endpoint
LIMIT = 5
# test period in seconds for endpoint limit
PERIOD = 60


@pytest.fixture(scope="module")
def limit():
    """
    testing route limit (num requests)
    """
    return LIMIT


@pytest.fixture(scope="module")
def period():
    """
    testing period (in seconds)
    """
    return PERIOD


@pytest.fixture(scope="module")
def client():
    """
    pytest fixture that creates & returns test
    flask client
    """
    # create flask app
    app = Flask(__name__)
    # init flask_rl
    flask_rl = FlaskRL(
        app,
        dbname="testing.flask_rl.db",
        webhook_url=os.environ.get("TEST_WEBHOOK_URL", None),
    )
    # define web app with flask_rl
    @app.route("/")
    @flask_rl.limit(limit=LIMIT, period=PERIOD)
    def home():
        return "home"

    @app.route("/random")
    @flask_rl.limit(limit=LIMIT, period=PERIOD)
    def random():
        return "random"

    # yield test client
    yield app.test_client()
    # flask_rl db path
    flask_rl_db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "testing.flask_rl.db",
    )
    # remove flask_rl db
    os.remove(flask_rl_db_path)
