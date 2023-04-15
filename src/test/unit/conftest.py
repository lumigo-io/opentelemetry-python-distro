import pytest

from lumigo_core.scrubbing import get_omitting_regex


@pytest.fixture(autouse=True)
def clear_cache():
    get_omitting_regex.cache_clear()
