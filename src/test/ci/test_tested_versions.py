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


def test_parse_version():
    assert parse_version("  1.2.3  # test!") == SemanticVersion(
        True, "1.2.3  # test!", 1, 2, 3, "", "test!"
    )

    # We disregard comments in the equality check
    assert parse_version("!1.2.3") == SemanticVersion(
        False, "1.2.3  # test!", 1, 2, 3, "", "test!"
    )

    # We preserve the actual version string for semantic versions
    assert (
        SemanticVersion(False, "   1.2.3  # test!", 1, 2, 3, "", "test!").version
        == "   1.2.3  # test!"
    )

    # We disregard support in equality checks
    assert parse_version("!1.2.3") == parse_version("1.2.3")

    # We disregard support in ordering
    assert parse_version("!1.2.3") < parse_version("1.2.4")

    # Non-semantic versions are considered always larger than semantic ones
    assert parse_version("!1.2.3") < parse_version("0.1")

    # Non-semantic versions are orders lexicographically
    assert parse_version("0.11") < parse_version("0.2")

    # Test version sorting
    assert sorted(
        [parse_version("1.3.5"), parse_version("0.2"), parse_version("1.2.3")]
    ) == [parse_version("1.2.3"), parse_version("1.3.5"), parse_version("0.2")]


def test_version_ranges():
    # Start simple :-)
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("0.0.2"),
                parse_version("0.0.3"),
            ]
        )
    ) == ["0.0.1~0.0.3"]

    # Simple range break within same minor
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("0.0.2"),
                parse_version("!0.0.3"),
                parse_version("0.0.4"),
                parse_version("0.0.5"),
            ]
        )
    ) == ["0.0.1~0.0.2", "0.0.4~0.0.5"]

    # Simple range break within with minor jump
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("0.0.2"),
                parse_version("!0.0.3"),
                parse_version("0.0.4"),
                parse_version("0.1.1"),
            ]
        )
    ) == ["0.0.1~0.0.2", "0.0.4~0.1.1"]

    # Simple range break within with major jump
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("0.0.2"),
                parse_version("!0.0.3"),
                parse_version("0.0.4"),
                parse_version("1.0.0"),
            ]
        )
    ) == ["0.0.1~0.0.2", "0.0.4", "1.0.0"]

    # Test we skip correctly unsupported first version
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("!0.0.1"),
                parse_version("0.0.2"),
                parse_version("0.0.3"),
            ]
        )
    ) == ["0.0.2~0.0.3"]

    # Test we skip correctly unsupported multiple first versions
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("!0.0.1"),
                parse_version("!0.0.2"),
                parse_version("0.0.3"),
            ]
        )
    ) == ["0.0.3"]

    # Test we skip correctly unsupported last version
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("0.0.2"),
                parse_version("!0.0.3"),
            ]
        )
    ) == ["0.0.1~0.0.2"]

    # Test we skip correctly unsupported last versions
    assert _get_supported_version_ranges(
        TestedVersions(
            [
                parse_version("0.0.1"),
                parse_version("!0.0.2"),
                parse_version("!0.0.3"),
            ]
        )
    ) == ["0.0.1"]

    # Test we skip correctly versions
    assert _get_supported_version_ranges(
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
    ) == ["0.0.2~0.1.0", "1.0.1"]

    # Skipping non-semantic versions
    assert _get_supported_version_ranges(
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
    ) == ["0.0.2~0.1.0", "nonsemantic"]

    # Skipping all non-semantic versions
    assert _get_supported_version_ranges(
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
    ) == ["0.0.2~0.1.0"]

    # Multiple non-semantic versions
    assert _get_supported_version_ranges(
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
    ) == ["0.0.2~0.1.0", "nonsemantic1", "nonsemantic2"]
