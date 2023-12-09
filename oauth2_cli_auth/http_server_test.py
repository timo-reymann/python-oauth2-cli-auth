import threading
import urllib
from urllib.error import HTTPError

import pytest

from oauth2_cli_auth import OAuthCallbackHttpServer


def test_http_server_ok():
    server = OAuthCallbackHttpServer(5000)

    threading.Thread(target=server.handle_request).start()
    with urllib.request.urlopen("http://localhost:5000?code=foo") as response:
        content = response.read().decode("utf-8")


def test_http_server_bad_request():
    server = OAuthCallbackHttpServer(5000)

    threading.Thread(target=server.handle_request).start()
    with pytest.raises(HTTPError, match="HTTP Error 400: Bad Request") as e:
        with urllib.request.urlopen("http://localhost:5000") as response:
            content = response.read().decode("utf-8")
            assert "Oh snap" in content
