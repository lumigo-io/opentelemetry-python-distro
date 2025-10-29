from unittest.mock import Mock, patch


from lumigo_opentelemetry.resources.span_processor import LumigoExecutionTagProcessor
from lumigo_opentelemetry.utils.span_processor_utils import EXECUTION_TAGS_CONTEXT_KEY


def _make_hashable(obj):
    """Convert lists to tuples recursively for hashability in test comparisons."""
    if isinstance(obj, list):
        return tuple(_make_hashable(item) for item in obj)
    return obj


def _clear_execution_tags_context():
    from opentelemetry import context as otel_context

    # Set empty dict to clear any existing tags
    new_context = otel_context.set_value(EXECUTION_TAGS_CONTEXT_KEY, {})
    otel_context.attach(new_context)


def test_on_start_with_single_execution_tag():
    """Test that single execution tag is added to span when present in context."""
    _clear_execution_tags_context()

    from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    add_execution_tags({"env": "staging"})
    processor.on_start(mock_span)

    mock_span.set_attribute.assert_called_once_with(
        "lumigo.execution_tags.env", "staging"
    )


def test_on_start_without_execution_tags():
    """Test that no attribute is set when no execution tags are present."""
    _clear_execution_tags_context()

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    # Since no execution tags are set, the processor should not log any errors
    processor.on_start(mock_span)
    mock_span.set_attribute.assert_not_called()


def test_on_start_with_empty_execution_tags_dict():
    """Test that no attribute is set when execution tags dictionary is empty."""
    _clear_execution_tags_context()

    from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    with patch("lumigo_opentelemetry.utils.span_processor_utils.logger") as mock_logger:
        add_execution_tags({})  # Empty dict should be rejected by validation
        mock_logger.error.assert_called_once_with("No valid execution tags to add")

    processor.on_start(mock_span)
    mock_span.set_attribute.assert_not_called()


def test_on_start_with_empty_string_values():
    """Test that no attributes are set when values are empty strings (filtered out by validation)."""
    _clear_execution_tags_context()

    # Try to set execution tags with empty string values - should be filtered out
    from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    with patch("lumigo_opentelemetry.utils.span_processor_utils.logger") as mock_logger:
        add_execution_tags(
            {"env": "", "user": "   "}
        )  # These should be rejected by validation

        expected_calls = [
            "Empty or whitespace execution tag value: 'env', ''",
            "Empty or whitespace execution tag value: 'user', '   '",
            "No valid execution tags to add",
        ]

        actual_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        for expected_msg in expected_calls:
            assert (
                expected_msg in actual_calls
            ), f"Expected log message not found: {expected_msg}"

    processor.on_start(mock_span)

    # Verify no attributes were set (empty/whitespace values are filtered out)
    mock_span.set_attribute.assert_not_called()


def test_on_start_with_mixed_valid_invalid_execution_tags():
    """Test that only valid tags are set when mixed with invalid ones."""
    _clear_execution_tags_context()

    from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    with patch("lumigo_opentelemetry.utils.span_processor_utils.logger") as mock_logger:
        # Mix of valid and invalid execution tags
        add_execution_tags(
            {
                "valid_env": "prod",  # Valid
                "": "empty_key",  # Invalid - empty key (value is valid but key is empty)
                "valid_user": True,  # Valid
                "empty_value": "",  # Invalid - empty value
                123: "non_string_key",  # Invalid - non-string key
                "regions": ["us-east-1", "us-west-2"],  # Valid - Array
                "permissions": ("read", "write", "admin"),  # Valid - Tuple
                "version": 1,  # Valid - int
            }
        )

        # Verify error messages were logged for invalid entries only
        # Note: "" (empty key) fails key validation, so value is never checked
        expected_error_calls = [
            "Execution tag key must be a string and cannot be empty or whitespace: '123' (type: int)",
            "Execution tag key must be a string and cannot be empty or whitespace: '' (type: str)",
            "Empty or whitespace execution tag value: 'empty_value', ''",
        ]

        actual_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        for expected_msg in expected_error_calls:
            assert (
                expected_msg in actual_calls
            ), f"Expected log message not found: {expected_msg}"

    processor.on_start(mock_span)

    expected_calls = [
        (("lumigo.execution_tags.valid_env", "prod"), {}),
        (("lumigo.execution_tags.valid_user", True), {}),
        (("lumigo.execution_tags.regions", ["us-east-1", "us-west-2"]), {}),
        (
            ("lumigo.execution_tags.permissions", ["read", "write", "admin"]),
            {},
        ),  # tuple converted to list
        (("lumigo.execution_tags.version", 1), {}),
    ]

    actual_calls = mock_span.set_attribute.call_args_list
    assert len(actual_calls) == 5

    actual_calls_tuples = [
        tuple(_make_hashable(arg) for arg in call.args)
        + (tuple(sorted(call.kwargs.items())),)
        for call in actual_calls
    ]
    expected_calls_tuples = [
        tuple(_make_hashable(arg) for arg in args) + (tuple(sorted(kwargs.items())),)
        for args, kwargs in expected_calls
    ]

    assert set(actual_calls_tuples) == set(expected_calls_tuples)


def test_on_start_with_duplicate_execution_tag_keys():
    """Test that execution tags with duplicate keys are properly overwritten."""
    _clear_execution_tags_context()

    from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    # First, set some initial execution tags
    add_execution_tags({"env": "development", "user": "alice", "version": "1.0"})

    # Then, add execution tags with some overlapping keys and some new ones
    add_execution_tags(
        {
            "env": "production",  # This should overwrite "development"
            "user": "bob",  # This should overwrite "alice"
            "region": "us-east-1"  # This is a new key
            # "version" should remain as "1.0" since it's not updated
        }
    )

    processor.on_start(mock_span)

    # Verify the final state: updated values for duplicates, retained values for non-duplicates
    expected_calls = [
        (("lumigo.execution_tags.env", "production"), {}),  # Updated
        (("lumigo.execution_tags.user", "bob"), {}),  # Updated
        (("lumigo.execution_tags.version", "1.0"), {}),  # Retained from first call
        (("lumigo.execution_tags.region", "us-east-1"), {}),  # New
    ]

    actual_calls = mock_span.set_attribute.call_args_list
    assert len(actual_calls) == 4

    # Convert call objects to hashable tuples for comparison
    actual_calls_tuples = [
        call.args + (tuple(sorted(call.kwargs.items())),) for call in actual_calls
    ]
    expected_calls_tuples = [
        args + (tuple(sorted(kwargs.items())),) for args, kwargs in expected_calls
    ]

    # Compare as sets (order doesn't matter)
    assert set(actual_calls_tuples) == set(expected_calls_tuples)


@patch("lumigo_opentelemetry.utils.span_processor_utils._get_execution_tags")
def test_on_start_exception_handling(mock_get_execution_tags):
    """Test that exceptions during tag retrieval don't break span creation."""
    _clear_execution_tags_context()

    # Make _get_execution_tags raise an exception
    mock_get_execution_tags.side_effect = Exception("Tag retrieval error")

    processor = LumigoExecutionTagProcessor()
    mock_span = Mock()

    # Call on_start - should not raise an exception
    processor.on_start(mock_span)

    # Verify no attribute was set on the span
    mock_span.set_attribute.assert_not_called()
