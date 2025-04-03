import json
import time
import urllib
from urllib.error import URLError
from typing import Union


def _urlopen_with_backoff(url, max_retries=3, base_delay=1, timeout=15):
    retries = 0

    while retries < max_retries:
        try:
            response = urllib.request.urlopen(url, timeout=timeout)
            return response
        except Exception:
            retries += 1
            delay = base_delay * (2 ** retries)
            time.sleep(delay)

    raise URLError(f"Failed to open URL after {max_retries} retries")


def _load_json(url_or_request: Union[str, urllib.request.Request]) -> dict:
    with _urlopen_with_backoff(url_or_request) as response:
        response_data = response.read().decode('utf-8')
        json_response = json.loads(response_data)
    return json_response
