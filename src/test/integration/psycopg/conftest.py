from test.test_utils.spans_parser import SpansContainer

import pytest


@pytest.fixture(autouse=True)
def increment_spans_counter():
    SpansContainer.update_span_offset()
