import attr
from ci.tested_versions_utils import (
    SemanticVersion,
    TestedVersions,
    parse_version,
    _get_supported_version_ranges,
)


def test_tested_versions_sorts_on_constructor():
    assert TestedVersions(
        [
            parse_version("0.0.1"),
            parse_version("0.0.3"),
            parse_version("0.0.2"),
        ]
    ).versions == [
        parse_version("0.0.1"),
        parse_version("0.0.2"),
        parse_version("0.0.3"),
    ]


def test_tested_versions_is_frozen():
    try:
        TestedVersions([]).versions = [parse_version("0.0.1")]
        raise Exception("We should not have gotten here")
    except attr.exceptions.FrozenInstanceError:
        pass


def test_parse_supported_semantic_version():
    assert parse_version("  1.2.3  # test!") == SemanticVersion(
        True, "1.2.3  # test!", 1, 2, 3, "", "test!"
    )


def test_parse_semantic_version_equality_ignores_supported_flag():
    assert parse_version("!1.2.3") == SemanticVersion(
        False, "1.2.3  # test!", 1, 2, 3, "", "test!"
    )


def test_parse_semantic_version_equality_ignores_comment():
    # We disregard support in equality checks
    assert parse_version("1.2.3 # comment") == parse_version("1.2.3")


def test_parse_semantic_version_preserve_original_version_string():
    assert (
        SemanticVersion(False, "   1.2.3  # test!", 1, 2, 3, "", "test!").version
        == "   1.2.3  # test!"
    )


def test_semantic_version_sorting_ignores_supported_flag():
    assert parse_version("!1.2.3") < parse_version("1.2.4")


def test_semantic_version_always_smaller_than_non_semantic_version():
    assert parse_version("!1.2.3") < parse_version("0.1")


def test_non_semantic_versions_are_sorted_lexicographically():
    assert parse_version("0.11") < parse_version("0.2")


def test_sorting_mixed_version_types():
    assert sorted(
        [parse_version("1.3.5"), parse_version("0.2"), parse_version("1.2.3")]
    ) == [parse_version("1.2.3"), parse_version("1.3.5"), parse_version("0.2")]


def test_consecutive_semantic_version_range():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                ]
            )
        )
        == ["0.0.1~0.0.3"]
    )


def test_semantic_version_ranges_with_break():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("!0.0.3"),
                    parse_version("0.0.4"),
                    parse_version("0.0.5"),
                ]
            )
        )
        == ["0.0.1~0.0.2", "0.0.4~0.0.5"]
    )


def test_semantic_version_ranges_with_break_and_minor_jump():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("!0.0.3"),
                    parse_version("0.0.4"),
                    parse_version("0.1.1"),
                ]
            )
        )
        == ["0.0.1~0.0.2", "0.0.4~0.1.1"]
    )


def test_semantic_version_ranges_with_break_and_major_jump():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("!0.0.3"),
                    parse_version("0.0.4"),
                    parse_version("1.0.0"),
                ]
            )
        )
        == ["0.0.1~0.0.2", "0.0.4", "1.0.0"]
    )


def test_semantic_version_ranges_with_unsupported_beginning():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                ]
            )
        )
        == ["0.0.2~0.0.3"]
    )


def test_semantic_version_ranges_with_multiple_unsupported_beginning():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("!0.0.2"),
                    parse_version("0.0.3"),
                ]
            )
        )
        == ["0.0.3"]
    )


def test_semantic_version_ranges_with_unsupported_ending():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("!0.0.3"),
                ]
            )
        )
        == ["0.0.1~0.0.2"]
    )


def test_semantic_version_ranges_with_multiple_unsupported_ending():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("0.0.1"),
                    parse_version("!0.0.2"),
                    parse_version("!0.0.3"),
                ]
            )
        )
        == ["0.0.1"]
    )


def test_semantic_version_ranges_with_multiple_unsupported_beginning_and_breaks():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                    parse_version("0.1.0"),
                    parse_version("!0.1.1"),
                    parse_version("1.0.1"),
                ]
            )
        )
        == ["0.0.2~0.1.0", "1.0.1"]
    )


def test_skipping_non_semantic_versions():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                    parse_version("0.1.0"),
                    parse_version("!0.2"),
                    parse_version("nonsemantic"),
                ]
            )
        )
        == ["0.0.2~0.1.0", "nonsemantic"]
    )


def test_skipping_multiple_non_semantic_versions():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                    parse_version("0.1.0"),
                    parse_version("!0.2"),
                    parse_version("!nonsemantic"),
                ]
            )
        )
        == ["0.0.2~0.1.0"]
    )


def test_non_semantic_version_ranges():
    assert (
        _get_supported_version_ranges(
            TestedVersions(
                [
                    parse_version("!0.0.1"),
                    parse_version("0.0.2"),
                    parse_version("0.0.3"),
                    parse_version("0.1.0"),
                    parse_version("!0.2"),
                    parse_version("nonsemantic1"),
                    parse_version("nonsemantic2"),
                ]
            )
        )
        == ["0.0.2~0.1.0", "nonsemantic1", "nonsemantic2"]
    )
