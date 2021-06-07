"""
    test_flask_rl.py: actual tests for flask_rl
"""


def test_limiter_basic(client, limit):
    """
    test limiter returns 429 status code if limit exceeded
    """
    # make get requests more than the limit
    for _ in range(limit * 2):
        # get page
        response = client.get("/")
    # make request (past the limit)
    response = client.get("/")
    # assert response is valid
    assert response.status_code == 429


def test_limiter_other_route(client, limit):
    """
    test limiter returns 200 on route where limit not
    exceeded & returns 429 status code if limit exceeded
    """
    # make get requests more than the limit
    for _ in range(limit * 2):
        # get page
        response = client.get("/")
    # make request to another route whose
    # rate hasn't been exceeded
    response = client.get("/random")
    # assert response is valid
    assert response.status_code == 200
    # make request (past the limit)
    response = client.get("/")
    # assert response is valid
    assert response.status_code == 429
