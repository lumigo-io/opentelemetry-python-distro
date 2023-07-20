import logging

import pytest

from lumigo_core.scrubbing import get_omitting_regex
from lumigo_opentelemetry import logger


@pytest.fixture(autouse=True)
def clear_cache():
    get_omitting_regex.cache_clear()


@pytest.fixture(autouse=True)
def capture_all_logs(caplog):
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    caplog.set_level(logging.DEBUG, logger="lumigo")
