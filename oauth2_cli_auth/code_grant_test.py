from oauth2_cli_auth import OAuth2ClientInfo, get_auth_url


def test_get_auth_url():
    client_info = OAuth2ClientInfo(
        client_id="dummy",
        authorization_url="https://auth.com/oauth/authorize",
        token_url="https://auth.com/oauth/token",
        scopes=["openid", "profile"]
    )
    auth_url = get_auth_url(client_info, "http://localhost:123")
    assert auth_url == (
        'https://auth.com/oauth/authorize?client_id=dummy&redirect_uri=http://localhost:123&scope=openid '
        'profile&response_type=code'
    )
