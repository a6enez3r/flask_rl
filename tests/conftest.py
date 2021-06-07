"""
    conftest.py: contains pytest fixtures
"""
# sys
import os

# testing
import pytest

# flask
from flask import Flask

# limiter extension class
from flask_rl import Limiter

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
    # init limiter
    limiter = Limiter(app, dbname="testing.limiter.db")
    # define web app with limiter
    @app.route("/")
    @limiter.limit(limit=LIMIT, period=PERIOD)
    def home():
        return "home"

    @app.route("/random")
    @limiter.limit(limit=LIMIT, period=PERIOD)
    def random():
        return "random"

    # yield test client
    yield app.test_client()
    # limiter db path
    limiter_db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "testing.limiter.db",
    )
    # remove limiter db
    os.remove(limiter_db_path)
