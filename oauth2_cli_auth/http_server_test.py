import random
import threading
import urllib
from urllib.error import HTTPError

import pytest

from oauth2_cli_auth import OAuthCallbackHttpServer

PORT = 49152 + random.randrange(15000)

def test_http_server_ok():
    server = OAuthCallbackHttpServer(PORT, state="s")

    threading.Thread(target=server.handle_request).start()
    with urllib.request.urlopen(f"http://localhost:{PORT}?code=foo&state=s") as response:
        content = response.read().decode("utf-8")
        assert content is not None
    assert server.get_code() == "foo"
    server.server_close()


def test_http_server_bad_request():
    server = OAuthCallbackHttpServer(PORT)

    threading.Thread(target=server.handle_request).start()
    with pytest.raises(HTTPError, match="HTTP Error 400: Bad Request") as e:
        with urllib.request.urlopen(f"http://localhost:{PORT}") as response:
            content = response.read().decode("utf-8")
            assert "Oh snap" in content


@pytest.mark.parametrize("query", ["code=attacker", "code=attacker&state=wrong", "code=attacker&state=s&state=s"])
def test_http_server_rejects_missing_or_wrong_state(query):
    server = OAuthCallbackHttpServer(0, state="s")

    threading.Thread(target=server.handle_request).start()
    with pytest.raises(HTTPError, match="HTTP Error 400: Bad Request"):
        urllib.request.urlopen(f"http://localhost:{server.server_port}?{query}")
    assert server.get_code() is None
    server.server_close()


def test_http_server_binds_to_loopback_by_default():
    server = OAuthCallbackHttpServer(0)
    assert server.server_address[0] == "127.0.0.1"
    server.server_close()


def test_http_server_generates_random_state():
    first, second = OAuthCallbackHttpServer(0), OAuthCallbackHttpServer(0)
    assert first.state != second.state
    assert len(first.state) >= 32
    first.server_close()
    second.server_close()


def test_wait_for_code_ignores_forged_request_and_accepts_valid_one():
    server = OAuthCallbackHttpServer(0, state="s")
    port = server.server_port

    def requests():
        with pytest.raises(HTTPError):
            urllib.request.urlopen(f"http://localhost:{port}?code=attacker&state=wrong")
        urllib.request.urlopen(f"http://localhost:{port}?code=legit&state=s").read()

    threading.Thread(target=requests).start()
    assert server.wait_for_code(attempts=1, timeout_per_attempt=5) == "legit"
    server.server_close()
