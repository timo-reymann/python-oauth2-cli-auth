import random
import threading
import urllib
from urllib.error import HTTPError

import pytest

from oauth2_cli_auth import OAuthCallbackHttpServer

PORT = 49152 + random.randrange(15000)

def test_http_server_ok():
    server = OAuthCallbackHttpServer(PORT)

    threading.Thread(target=server.handle_request).start()
    with urllib.request.urlopen(f"http://localhost:{PORT}?code=foo") as response:
        content = response.read().decode("utf-8")
        assert content is not None


def test_http_server_bad_request():
    server = OAuthCallbackHttpServer(PORT)

    threading.Thread(target=server.handle_request).start()
    with pytest.raises(HTTPError, match="HTTP Error 400: Bad Request") as e:
        with urllib.request.urlopen(f"http://localhost:{PORT}") as response:
            content = response.read().decode("utf-8")
            assert "Oh snap" in content
