import base64
import urllib.parse
import urllib.request
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass

from oauth2_cli_auth._urllib_util import _load_json


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

    @staticmethod
    def from_oidc_endpoint(oidc_config_endpoint: str, client_id: str, scopes: list[str]):
        config = load_oidc_config(oidc_config_endpoint)
        return OAuth2ClientInfo(
            authorization_url=config.get("authorization_endpoint"),
            token_url=config.get("token_endpoint"),
            client_id=client_id,
            scopes=scopes,
        )


def load_oidc_config(odic_well_known_endpoint: str) -> dict:
    config = _load_json(odic_well_known_endpoint)
    return config


def open_browser(url: str, print_open_browser_instruction: Callable[[str], None] | None = print) -> None:
    """
    Open browser using webbrowser module and show message about URL open
    :param print_open_browser_instruction: Callback to print the instructions to open the browser. Set to None in order to supress the output.
    :param url: URL to open and display
    :return: None
    """
    if print_open_browser_instruction is not None:
        print_open_browser_instruction(f"Open your browser at\n{url}")
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


def exchange_code_for_response(
        client_info: OAuth2ClientInfo,
        redirect_uri: str,
        code: str,
) -> dict:
    """
    Exchange a code for an access token using the endpoints from client info and return the entire response

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param access_token_field: Name of the field containing the access token to use. This might differ depending on
                              the provider you are using. For example for Auth0 you have to set this to id_token
    :return: Response from OAuth2 endpoint
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
    json_response = _load_json(request)

    return json_response


def exchange_code_for_access_token(
        client_info: OAuth2ClientInfo,
        redirect_uri: str,
        code: str,
        access_token_field: str = "access_token"
) -> str:
    """
    Exchange a code for an access token using the endpoints from client info

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param access_token_field: Name of the field containing the access token to use. This might differ depending on
                               the provider you are using. For example for Auth0 you have to set this to id_token
    :return: Extracted access token from response
    """
    json_response = exchange_code_for_response(client_info, redirect_uri, code)

    return json_response.get(access_token_field)
