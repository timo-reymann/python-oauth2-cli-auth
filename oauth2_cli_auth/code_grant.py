"""
Functionality to work with OAuth2 code grant
"""
import base64
import hashlib
import secrets
import urllib.parse
import urllib.request
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

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

    client_secret: str | None
    """Secret of the client to request for"""

    scopes: list[str]
    """List of scopes to request"""

    @staticmethod
    def from_oidc_endpoint(oidc_config_endpoint: str, client_id: str, scopes: list[str] = [], client_secret: str | None = None) -> "OAuth2ClientInfo":
        """
        Create client information object from well known endpoint in format as specified in
        https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata

        :param oidc_config_endpoint: Endpoint to load
        :param client_id: Client ID to use
        :param scopes: Scopes to add to OAuth2 authorization requests
        :return: OAuth2ClientInfo containing parsed information from endpoint
        """
        config = load_oidc_config(oidc_config_endpoint)
        return OAuth2ClientInfo(
            authorization_url=config.get("authorization_endpoint"),
            token_url=config.get("token_endpoint"),
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
        )


def load_oidc_config(odic_well_known_endpoint: str) -> dict:
    """
    Load OIDC configuration from the well known configuration endpoint

    :param odic_well_known_endpoint: Endpoint to load configuration from
    """
    config = _load_json(odic_well_known_endpoint)
    return config


def open_browser(url: str, print_open_browser_instruction: Optional[Callable[[str], None]] = print) -> None:
    """
    Open browser using webbrowser module and show message about URL open

    :param print_open_browser_instruction: Callback to print the instructions to open the browser. Set to None in order to supress the output.
    :param url: URL to open and display
    :return: None
    """
    if print_open_browser_instruction is not None:
        print_open_browser_instruction(f"Open your browser at\n{url}")
    webbrowser.open(url)


def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate a PKCE (RFC 7636) code verifier and its S256 code challenge

    :return: Tuple of (code_verifier, code_challenge)
    """
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def get_auth_url(client_info: OAuth2ClientInfo, redirect_uri: str, state: Optional[str] = None,
                 code_challenge: Optional[str] = None) -> str:
    """
    Build authorization url for browser

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param state: Opaque value to protect the callback against forged requests. Providers echo it back on the redirect.
    :param code_challenge: PKCE S256 code challenge, see generate_pkce_pair
    :return: Ready to use URL
    """
    params = {
        "client_id": client_info.client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(client_info.scopes),
        "response_type": "code",
    }
    if state is not None:
        params["state"] = state
    if code_challenge is not None:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    return f"{client_info.authorization_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_response(
        client_info: OAuth2ClientInfo,
        redirect_uri: str,
        code: str,
        code_verifier: Optional[str] = None,
) -> dict:
    """
    Exchange a code for an access token using the endpoints from client info and return the entire response

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param code_verifier: PKCE code verifier matching the code challenge of the authorization request
    :return: Response from OAuth2 endpoint
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{client_info.client_id}:{client_info.client_secret if client_info.client_secret is not None else ''}".encode()).decode(),
    }

    data = {
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    if code_verifier is not None:
        data["code_verifier"] = code_verifier
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(client_info.token_url, data=encoded_data, headers=headers)
    json_response = _load_json(request)

    return json_response

def refresh_access_token(
        client_info: OAuth2ClientInfo,
        refresh_token: str,
) -> dict:
    """
    Refresh an access token using the endpoints from client info

    :param client_info: Info about oauth2 client
    :param refresh_token: Refresh token to use
    :return: Response from OAuth2 endpoint
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{client_info.client_id}:{client_info.client_secret if client_info.client_secret is not None else ''}".encode()).decode(),
    }

    data = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(client_info.token_url, data=encoded_data, headers=headers)
    json_response = _load_json(request)

    return json_response

def exchange_code_for_access_token(
        client_info: OAuth2ClientInfo,
        redirect_uri: str,
        code: str,
        access_token_field: str = "access_token",
        code_verifier: Optional[str] = None,
) -> str:
    """
    Exchange a code for an access token using the endpoints from client info

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param access_token_field: Name of the field containing the access token to use. This might differ depending on
                               the provider you are using. For example for Auth0 you have to set this to id_token
    :param code_verifier: PKCE code verifier matching the code challenge of the authorization request
    :return: Extracted access token from response
    """
    json_response = exchange_code_for_response(client_info, redirect_uri, code, code_verifier)

    return json_response.get(access_token_field)
