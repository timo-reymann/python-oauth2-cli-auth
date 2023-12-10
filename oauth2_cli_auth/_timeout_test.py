import time

import pytest

from oauth2_cli_auth._timeout import _method_with_timeout, TimeoutException


def test_timeout():
    def method():
        time.sleep(10)

    with pytest.raises(TimeoutException):
        _method_with_timeout(method, 1)
