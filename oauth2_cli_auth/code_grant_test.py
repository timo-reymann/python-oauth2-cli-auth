import io
import urllib
from unittest.mock import patch

from oauth2_cli_auth import OAuth2ClientInfo, get_auth_url, exchange_code_for_access_token

client_info = OAuth2ClientInfo(
    client_id="dummy",
    authorization_url="https://auth.com/oauth/authorize",
    token_url="https://auth.com/oauth/token",
    scopes=["openid", "profile"]
)


def test_get_auth_url():
    auth_url = get_auth_url(client_info, "http://localhost:123")
    assert auth_url == (
        'https://auth.com/oauth/authorize?client_id=dummy&redirect_uri=http://localhost:123&scope=openid '
        'profile&response_type=code'
    )


def test_exchange_code_for_access_token():
    data = io.BytesIO(b'{"access_token": "the_token"}')
    with patch.object(urllib.request, 'urlopen', return_value=data):
        assert "the_token" == exchange_code_for_access_token(client_info, "http://localhost:123", "code")
