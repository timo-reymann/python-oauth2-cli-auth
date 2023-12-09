from oauth2_cli_auth import OAuthCallbackHttpServer, get_auth_url, exchange_code_for_access_token, OAuth2ClientInfo, \
    open_browser


def get_access_token_with_browser_open(client_info: OAuth2ClientInfo, server_port: int = 8080) -> str:
    """
    Provides a simplified API to:

    - Spin up the callback server
    - Open the browser with the authorization URL
    - Wait for the code to arrive
    - Get access token from code
    :param client_info: Client Info for Oauth2 Interaction
    :param server_port: Port of the local web server to spin up
    :return: Access Token
    """
    callback_server = OAuthCallbackHttpServer(server_port)
    auth_url = get_auth_url(client_info, callback_server.callback_url)
    open_browser(auth_url)
    code = callback_server.wait_for_code()
    if code is None:
        raise ValueError("No code could be obtained from browser callback page")
    return exchange_code_for_access_token(client_info, callback_server.callback_url, code)
