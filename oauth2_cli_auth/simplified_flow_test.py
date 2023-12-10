import io
import urllib
import webbrowser
from unittest.mock import patch

from oauth2_cli_auth import get_access_token_with_browser_open, OAuth2ClientInfo

client_info = OAuth2ClientInfo(
    client_id="dummy",
    authorization_url="http://auth.com/oauth/authorize",
    token_url="http://auth.com/oauth/token",
    scopes=["openid", "profile"]
)


@patch('webbrowser.open')
@patch("oauth2_cli_auth.http_server.OAuthCallbackHttpServer.get_code")
@patch("oauth2_cli_auth.http_server.OAuthCallbackHttpServer.handle_request")
def test_get_access_token_with_browser_open(webbrowser_open, get_code, handle_request):
    with patch.object(urllib.request, 'urlopen', return_value=io.BytesIO(b'{"access_token": "the_token"}')):
        get_code.return_value = "code"
        assert "the_token" == get_access_token_with_browser_open(client_info, 8080)

    assert get_code.call_count == 2
    assert handle_request.call_count == 1