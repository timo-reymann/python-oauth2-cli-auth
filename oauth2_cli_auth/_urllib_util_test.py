import io
from unittest.mock import Mock, patch
from urllib.error import URLError

from oauth2_cli_auth._urllib_util import _urlopen_with_backoff, _load_json


def test_urlopen_with_backoff(create_urlopen_mock):
    response_mock = Mock()
    with patch('urllib.request.urlopen', side_effect=[URLError(""), response_mock]) as mock_urlopen:
        response = _urlopen_with_backoff("http://example.com", max_retries=3)
        assert response == response_mock
    assert mock_urlopen.call_count == 2


def test_load_json(create_urlopen_mock):
    with create_urlopen_mock(io.BytesIO(b'{"a":"b"}')):
        content = _load_json("https://example.com")
        assert 'a' in content
        assert 'b' == content.get("a")
