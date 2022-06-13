import pytest

from test.test_utils.spans_parser import SpansContainer


@pytest.fixture(autouse=True)
def increment_spans_counter():
    SpansContainer.increment_spans()
