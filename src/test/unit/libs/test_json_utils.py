import datetime
from collections import OrderedDict
from decimal import Decimal

import pytest
from src.lumigo_opentelemetry.libs.json_utils import (
    SKIP_SCRUBBING_KEYS,
    TRUNCATE_SUFFIX,
    dump,
    LUMIGO_SECRET_MASKING_REGEX,
    get_omitting_regex,
)


@pytest.fixture(autouse=True)
def remove_caches(monkeypatch):
    get_omitting_regex.cache_clear()


@pytest.mark.parametrize(
    ("value", "output"),
    [
        ("aa", '"aa"'),  # happy flow - string
        (None, "null"),  # happy flow - None
        ("a" * 101, '"' + "a" * 99 + "...[too long]"),  # simple long string
        ({"a": "a"}, '{"a": "a"}'),  # happy flow - dict
        ({"a": set([1])}, '{"a": "{1}"}'),  # dict that can't be converted to json
        (b"a", '"a"'),  # bytes that can be decoded
        (
            b"\xff\xfea\x00",
            "\"b'\\\\xff\\\\xfea\\\\x00'\"",
        ),  # bytes that can't be decoded
        (
            {1: Decimal(1)},
            '{"1": 1.0}',
        ),  # decimal should be serializeable  (like in AWS!)
        ({"key": "b"}, '{"key": "****"}'),  # simple omitting
        ({"a": {"key": "b"}}, '{"a": {"key": "****"}}'),  # inner omitting
        ({"a": {"key": "b" * 100}}, '{"a": {"key": "****"}}'),  # long omitting
        ({"a": "b" * 300}, f'{{"a": "{"b" * 93}...[too long]'),  # long key
        ('{"a": "b"}', '{"a": "b"}'),  # string which is a simple json
        ('{"a": {"key": "b"}}', '{"a": {"key": "****"}}'),  # string with inner omitting
        ("{1: ", '"{1: "'),  # string which is not json but look like one
        (b'{"password": "abc"}', '{"password": "****"}'),  # omit of bytes
        (
            {"a": '{"password": 123}'},
            '{"a": "{\\"password\\": 123}"}',
        ),  # ignore inner json-string
        ({None: 1}, '{"null": 1}'),
        ({"1": datetime.datetime(1994, 4, 22)}, '{"1": "1994-04-22 00:00:00"}'),
        (
            OrderedDict({"a": "b", "key": "123"}),
            '{"a": "b", "key": "****"}',
        ),  # OrderedDict
        (  # Skip scrubbing
            {SKIP_SCRUBBING_KEYS[0]: {"password": 1}},
            f'{{"{SKIP_SCRUBBING_KEYS[0]}": {{"password": 1}}}}',
        ),
        (
            [{"password": 1}, {"a": "b"}],
            '[{"password": "****"}, {"a": "b"}]',
        ),  # list of dicts
        (  # Dict of long list
            {"a": [{"key": "value", "password": "value", "b": "c"}]},
            '{"a": [{"key": "****", "password": "****", "b": "c"}]}',
        ),
        (  # Multiple nested lists
            {"a": [[[{"c": [{"key": "v"}]}], [{"c": [{"key": "v"}]}]]]},
            '{"a": [[[{"c": [{"key": "****"}]}], [{"c": [{"key": "****"}]}]]]}',
        ),
        (  # non jsonable
            {"set"},
            "{'set'}",
        ),
        (  # redump already dumped and truncated json (avoid re-escaping)
            f'{{"a": "b{TRUNCATE_SUFFIX}',
            f'{{"a": "b{TRUNCATE_SUFFIX}',
        ),
    ],
)
def test_lumigo_dumps(value, output):
    assert dump(value, max_size=100) == output


@pytest.mark.parametrize(
    ("value", "omit_skip_path", "output"),
    [
        ({"a": "b", "Key": "v"}, ["Key"], '{"a": "b", "Key": "v"}'),  # Not nested
        (  # Nested with list
            {"R": [{"o": {"key": "value"}}]},
            ["R", "o", "key"],
            '{"R": [{"o": {"key": "value"}}]}',
        ),
        (  # Doesnt affect other paths
            {"a": {"key": "v"}, "b": {"key": "v"}},
            ["a", "key"],
            '{"a": {"key": "v"}, "b": {"key": "****"}}',
        ),
        (  # Nested items not affected
            {"key": {"password": "v"}},
            ["key"],
            '{"key": {"password": "****"}}',
        ),
        (  # Happy flow - nested case
            {"key": {"password": "v"}},
            ["key", "password"],
            '{"key": {"password": "v"}}',
        ),
        (
            {"a": {"key": "c"}},
            ["key"],
            '{"a": {"key": "****"}}',
        ),  # Affect only the full path
    ],
)
def test_lumigo_dumps_with_omit_skip(value, omit_skip_path, output):
    assert dump(value, omit_skip_path=omit_skip_path) == output


def test_lumigo_dumps_enforce_jsonify_raise_error():
    with pytest.raises(TypeError):
        assert dump({"a": set()}, max_size=100, enforce_jsonify=True)


def test_lumigo_dumps_no_regexes(monkeypatch):
    monkeypatch.setenv(LUMIGO_SECRET_MASKING_REGEX, "[]")
    result = dump({"key": "123"}, max_size=100, enforce_jsonify=True)
    assert result == '{"key": "123"}'


def test_lumigo_dumps_omit_keys_environment(monkeypatch):
    monkeypatch.setenv(LUMIGO_SECRET_MASKING_REGEX, '[".*evilPlan.*"]')
    value = {"password": "abc", "evilPlan": {"take": "over", "the": "world"}}
    assert dump(value, max_size=100) == '{"password": "abc", "evilPlan": "****"}'
