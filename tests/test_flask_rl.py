
def test_limiter(client, limit, period):
    """test limiter returns 429 status code if limit exceeded"""
    # make get requests more than the limit
    for _ in range(10):
        # get page
        response = client.get("/")
    # make request (past the limit)
    response = client.get("/")
    # assert response is valid
    assert response.status_code == 429