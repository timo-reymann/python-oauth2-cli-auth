import urllib
from unittest.mock import patch

import pytest


@pytest.fixture
def create_urlopen_mock():
    def mock(buffer):
        return patch.object(urllib.request, 'urlopen', return_value=buffer)

    return mock
