import io
import urllib
from unittest.mock import patch

from oauth2_cli_auth import OAuth2ClientInfo, get_auth_url, exchange_code_for_access_token, load_oidc_config
from oauth2_cli_auth.code_grant import exchange_code_for_response, refresh_access_token

REDIRECT_URI = "http://localhost:123"

client_info = OAuth2ClientInfo(
    client_id="dummy",
    client_secret=None,
    authorization_url="https://auth.com/oauth/authorize",
    token_url="https://auth.com/oauth/token",
    scopes=["openid", "profile"],
)


def test_get_auth_url():
    auth_url = get_auth_url(client_info, REDIRECT_URI)
    assert auth_url == (
        f'https://auth.com/oauth/authorize?client_id=dummy&redirect_uri={REDIRECT_URI}&scope=openid+'
        'profile&response_type=code'
    )

def test_exchange_code_for_response(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"access_token":"the_token","token_type":"Bearer","expires_in":3600,"refresh_token":"the_refresh_token","scope":"create"}')):
        response = exchange_code_for_response(client_info, REDIRECT_URI, "code")
        assert "the_token" == response.get("access_token")
        assert "Bearer" == response.get("token_type")
        assert 3600 == response.get("expires_in")
        assert "the_refresh_token" == response.get("refresh_token")
        assert "create" == response.get("scope")

def test_refresh_access_token(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"access_token":"the_token","token_type":"Bearer","expires_in":3600,"refresh_token":"the_refresh_token"}')):
        response = refresh_access_token(client_info, "the_refresh_token")
        assert "the_token" == response.get("access_token")
        assert "Bearer" == response.get("token_type")
        assert 3600 == response.get("expires_in")
        assert "the_refresh_token" == response.get("refresh_token")

def test_exchange_code_for_access_token(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"access_token": "the_token"}')):
        assert "the_token" == exchange_code_for_access_token(client_info, REDIRECT_URI, "code")

def test_load_oidc_config(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"token_endpoint": "https://gitlab.com/oauth/token","authorization_endpoint": "https://gitlab.com/oauth/authorize"}')):
        oidc_config = load_oidc_config("https://gitlab.com/.well-known/openid-configuration")
        assert "https://gitlab.com/oauth/token" == oidc_config.get("token_endpoint")
        assert "https://gitlab.com/oauth/authorize" == oidc_config.get("authorization_endpoint")


def test_client_info_from_oidc_endpoint(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"token_endpoint": "https://gitlab.com/oauth/token","authorization_endpoint": "https://gitlab.com/oauth/authorize"}')):
        client_info = OAuth2ClientInfo.from_oidc_endpoint(
            "https://gitlab.com/.well-known/openid-configuration",
            client_id="test-client",
            scopes=["openid"]
        )
        assert "test-client" == client_info.client_id
        assert ["openid"] == client_info.scopes
        assert "https://gitlab.com/oauth/token" == client_info.token_url
        assert "https://gitlab.com/oauth/authorize" == client_info.authorization_url
