import traceback

from oauth2_cli_auth import get_access_token_with_browser_open, OAuth2ClientInfo

if __name__ == "__main__":
    client_info = OAuth2ClientInfo(
        client_id="ce3f166bb9d5ce25d666b17f66449afff83d2fc56f42a5d62194ee5c847d8b13",
        authorization_url="https://gitlab.com/oauth/authorize",
        token_url="https://gitlab.com/oauth/token",
        scopes=["api"]
    )

    try:
        token = get_access_token_with_browser_open(client_info)
        print(f"Obtained token '{token}'")
    except ValueError:
        print(traceback.print_exc())
