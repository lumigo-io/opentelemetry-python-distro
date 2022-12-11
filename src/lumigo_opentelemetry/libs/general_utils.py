try:
    from collections import Iterable
except ImportError:
    # collections.Iterables was removed in Python 3.10
    from collections.abc import Iterable

from contextlib import contextmanager
from typing import Union, Generator, Optional, TypeVar, List
import os

from lumigo_opentelemetry import logger

from opentelemetry.sdk.environment_variables import (
    OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT,
    OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT,
)

DEFAULT_MAX_ENTRY_SIZE = 2048

T = TypeVar("T")


@contextmanager
def lumigo_safe_execute(part_name: str = "") -> Generator[None, None, None]:
    try:
        yield
    except Exception as e:
        logger.exception(
            f"An exception occurred in lumigo's code {part_name}", exc_info=e
        )


def safe_split_get(
    string: str, sep: str, index: int, default: Optional[str] = None
) -> Optional[str]:
    """
    This function splits the given string using the sep, and returns the organ in the `index` place.
    If such index doesn't exist, returns default.
    """
    if not isinstance(string, str):
        return default
    return safe_get_list(string.split(sep), index, default)


def safe_get_list(
    lst: List[T], index: Union[int, str], default: Optional[T] = None
) -> Optional[T]:
    """
    This function return the organ in the `index` place from the given list.
    If this values doesn't exist, return default.
    """
    if isinstance(index, str):
        try:
            index = int(index)
        except ValueError:
            return default
    if not isinstance(lst, Iterable):
        return default
    return lst[index] if len(lst) > index else default


def get_max_size() -> int:
    """
    This function return the max size by environment variables.
    If this values doesn't exist, return default size.
    """
    return int(
        os.environ.get(
            OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT,
            os.environ.get(OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT, DEFAULT_MAX_ENTRY_SIZE),
        )
    )
