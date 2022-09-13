import json
import os
import decimal
import re
from collections import OrderedDict
from decimal import Decimal
from functools import lru_cache, reduce
from typing import Any, Optional, List, TypeVar, Pattern, Dict, Tuple

from lumigo_opentelemetry.libs.general_utils import get_max_size


TRUNCATE_SUFFIX = "...[too long]"
LUMIGO_SECRET_MASKING_REGEX = "LUMIGO_SECRET_MASKING_REGEX"
Container = TypeVar("Container", Dict[Any, Any], List[Any])
EXECUTION_TAGS_KEY = "lumigo_execution_tags_no_scrub"
SKIP_SCRUBBING_KEYS = [EXECUTION_TAGS_KEY]


OMITTING_KEYS_REGEXES = [
    ".*pass.*",
    ".*key.*",
    ".*secret.*",
    ".*credential.*",
    "SessionToken",
    "x-amz-security-token",
    "Signature",
    "Authorization",
]


@lru_cache(maxsize=1)
def get_omitting_regex() -> Optional[Pattern[str]]:
    if LUMIGO_SECRET_MASKING_REGEX in os.environ:
        given_regexes = json.loads(os.environ[LUMIGO_SECRET_MASKING_REGEX])
    else:
        given_regexes = OMITTING_KEYS_REGEXES
    if not given_regexes:
        return None
    return re.compile(fr"({'|'.join(given_regexes)})", re.IGNORECASE)


def _recursive_omitting(
    prev_result: Tuple[Container, int],
    item: Tuple[Optional[str], Any],
    regex: Optional[Pattern[str]],
    enforce_jsonify: bool,
    decimal_safe: bool = False,
    omit_skip_path: Optional[List[str]] = None,
) -> Tuple[Container, int]:
    """
    This function omitting keys until the given max_size.
    This function should be used in a reduce iteration over dict.items().

    :param prev_result: the reduce result until now: the current dict and the remaining space
    :param item: the next yield from the iterator dict.items()
    :param regex: the regex of the keys that we should omit
    :param enforce_jsonify: should we abort if the object can not be jsonify.
    :param decimal_safe: should we accept decimal values
    :return: the intermediate result, after adding the current item (recursively).
    """
    key, value = item
    d, free_space = prev_result
    if free_space < 0:
        return d, free_space
    should_skip_key = False
    if isinstance(d, dict) and omit_skip_path:
        should_skip_key = omit_skip_path[0] == key
        omit_skip_path = omit_skip_path[1:] if should_skip_key else None
    if key in SKIP_SCRUBBING_KEYS:
        new_value = value
        free_space -= (
            len(value) if isinstance(value, str) else len(aws_dump({key: value}))
        )
    elif isinstance(key, str) and regex and regex.match(key) and not should_skip_key:
        new_value = "****"
        free_space -= 4
    elif isinstance(value, (dict, OrderedDict)):
        new_value, free_space = reduce(
            lambda p, i: _recursive_omitting(
                p, i, regex, enforce_jsonify, omit_skip_path=omit_skip_path
            ),
            value.items(),
            ({}, free_space),
        )
    elif isinstance(value, decimal.Decimal):
        new_value = float(value)
        free_space -= 5
    elif isinstance(value, list):
        new_value, free_space = reduce(
            lambda p, i: _recursive_omitting(
                p, (None, i), regex, enforce_jsonify, omit_skip_path=omit_skip_path
            ),
            value,
            ([], free_space),
        )
    elif isinstance(value, str):
        new_value = value
        free_space -= len(new_value)
    else:
        try:
            free_space -= len(aws_dump({key: value}, decimal_safe=decimal_safe))
            new_value = value
        except TypeError:
            if enforce_jsonify:
                raise
            new_value = str(value)
            free_space -= len(new_value)
    if isinstance(d, list):
        d.append(new_value)
    else:
        d[key] = new_value
    return d, free_space


def omit_keys(
    value: Dict[Any, Any],
    in_max_size: Optional[int] = None,
    regexes: Optional[Pattern[str]] = None,
    enforce_jsonify: bool = False,
    decimal_safe: bool = False,
    omit_skip_path: Optional[List[str]] = None,
) -> Tuple[Dict[Any, Any], bool]:
    """
    This function omit problematic keys from the given value.
    We do so in the following cases:
    * if the value is dictionary, then we omit values by keys (recursively)
    """
    regexes = regexes or get_omitting_regex()
    max_size = in_max_size or get_max_size()
    omitted, size = reduce(  # type: ignore
        lambda p, i: _recursive_omitting(
            prev_result=p,
            item=i,
            regex=regexes,
            enforce_jsonify=enforce_jsonify,
            decimal_safe=decimal_safe,
            omit_skip_path=omit_skip_path,
        ),
        value.items(),
        ({}, max_size),
    )
    return omitted, bool((size or 0) < 0)


def dump(
    to_dump: Any,
    decimal_safe: bool = False,
    omit_skip_path: Optional[List[str]] = None,
    max_size: Optional[int] = None,
    enforce_jsonify: bool = False,
) -> str:
    max_size = max_size or get_max_size()
    is_truncated = False

    if isinstance(to_dump, bytes):
        try:
            to_dump = to_dump.decode()
        except Exception:
            to_dump = str(to_dump)
    if isinstance(to_dump, str) and to_dump.startswith("{"):
        try:
            to_dump = json.loads(to_dump)
        except Exception:
            pass
    if isinstance(to_dump, dict):
        to_dump, is_truncated = omit_keys(
            value=to_dump,
            decimal_safe=decimal_safe,
            omit_skip_path=omit_skip_path,
            enforce_jsonify=enforce_jsonify,
        )
    elif isinstance(to_dump, list):
        size = 0
        organs = []
        for a in to_dump:
            organs.append(dump(a, omit_skip_path=omit_skip_path))
            size += len(organs[-1])
            if size > max_size:
                break
        return "[" + ", ".join(organs) + "]"
    try:
        if isinstance(to_dump, str) and to_dump.endswith(TRUNCATE_SUFFIX):
            return to_dump
        retval = aws_dump(to_dump, decimal_safe=decimal_safe)
    except TypeError:
        retval = str(to_dump)
    return (
        (retval[:max_size] + TRUNCATE_SUFFIX)
        if len(retval) >= max_size or is_truncated
        else retval
    )


def aws_dump(d: Any, decimal_safe: bool = False, **kwargs) -> str:  # type: ignore
    if decimal_safe:
        return json.dumps(d, cls=DecimalEncoder, **kwargs)
    return json.dumps(d, **kwargs)


class DecimalEncoder(json.JSONEncoder):
    # copied from python's runtime: runtime/lambda_runtime_marshaller.py:7-11
    def default(self, o: Any) -> float:
        if isinstance(o, Decimal):
            return float(o)
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )


def safe_convert_bytes_to_string(value: Any) -> Any:
    try:
        return value.decode("utf-8")
    except Exception:
        return value
