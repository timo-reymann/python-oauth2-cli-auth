import webbrowser
from dataclasses import dataclass
import urllib.request
import urllib.parse
import base64
import json


@dataclass
class OAuth2ClientInfo:
    """
    Metadata for Oauth2 client
    """
    authorization_url: str
    """Authorization URL to redirect the user to"""
    token_url: str
    """Token URL for fetching the access token"""
    client_id: str
    """Id of the client to request for"""
    scopes: list[str]
    """List of scopes to request"""


def open_browser(url: str) -> None:
    """
    Open browser using webbrowser module and show message about URL open
    :param url: URL to open and display
    :return: None
    """
    print(f"Open your browser at\n{url}")
    webbrowser.open(url)


def get_auth_url(client_info: OAuth2ClientInfo, redirect_uri: str) -> str:
    """
    Build authorization url for browser

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :return: Ready to use URL
    """
    return (f"{client_info.authorization_url}"
            f"?client_id={client_info.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={' '.join(client_info.scopes)}"
            f"&response_type=code")


def exchange_code_for_access_token(client_info: OAuth2ClientInfo, redirect_uri: str, code: str,
                                   access_token_field: str = "access_token") -> str:
    """
    Exchange a code for an access token using the endpoints from client info

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param access_token_field: Name of the field containing the access token to use. This might differ depending on
                               the provider you are using. For example for Auth0 you have to set this to id_token
    :return: Extracted access token from response
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{client_info.client_id}:".encode()).decode(),
    }

    data = {
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(client_info.token_url, data=encoded_data, headers=headers)
    with urllib.request.urlopen(request) as response:
        response_data = response.read().decode('utf-8')
        json_response = json.loads(response_data)

        access_token = json_response.get(access_token_field)

    return access_token
