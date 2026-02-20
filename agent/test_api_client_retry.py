import requests

from agent.api_client import BackendClient


class _Logger:
    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class _Response:
    def __init__(self, status_code=200):
        self.status_code = status_code


def test_post_with_retry_retries_then_succeeds(monkeypatch):
    client = BackendClient(_Logger())
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.ConnectionError("temporary failure")
        return _Response(status_code=200)

    monkeypatch.setattr("agent.api_client.requests.post", fake_post)
    monkeypatch.setattr("agent.api_client.time.sleep", lambda *_: None)

    response = client._post_with_retry("http://example.com")
    assert response.status_code == 200
    assert calls["count"] == 3


def test_post_with_retry_raises_after_max_attempts(monkeypatch):
    client = BackendClient(_Logger())
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        raise requests.ConnectionError("down")

    monkeypatch.setattr("agent.api_client.requests.post", fake_post)
    monkeypatch.setattr("agent.api_client.time.sleep", lambda *_: None)

    try:
        client._post_with_retry("http://example.com")
        assert False, "Expected ConnectionError"
    except requests.ConnectionError:
        assert calls["count"] >= 1
