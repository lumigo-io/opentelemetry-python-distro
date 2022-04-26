import pytest

from lumigo_wrapper.libs.json_utils import (
    get_omitting_regex,
)


@pytest.fixture(autouse=True)
def remove_caches(monkeypatch):
    get_omitting_regex.cache_clear()
