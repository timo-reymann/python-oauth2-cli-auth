import io
import urllib
from unittest.mock import patch

from oauth2_cli_auth import OAuth2ClientInfo, get_auth_url, exchange_code_for_access_token, load_oidc_config

client_info = OAuth2ClientInfo(
    client_id="dummy",
    client_secret="dummy",
    authorization_url="https://auth.com/oauth/authorize",
    token_url="https://auth.com/oauth/token",
    scopes=["openid", "profile"]
)


def test_get_auth_url():
    auth_url = get_auth_url(client_info, "http://localhost:123")
    assert auth_url == (
        'https://auth.com/oauth/authorize?client_id=dummy&redirect_uri=http://localhost:123&scope=openid+'
        'profile&response_type=code'
    )


def test_exchange_code_for_access_token(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"access_token": "the_token"}')):
        assert "the_token" == exchange_code_for_access_token(client_info, "http://localhost:123", "code")


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
