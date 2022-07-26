import pytest

from lumigo_opentelemetry.libs.json_utils import get_omitting_regex


@pytest.fixture(autouse=True)
def clear_cache():
    get_omitting_regex.cache_clear()
