try:
    from collections import Iterable
except ImportError:
    # collections.Iterables was removed in Python 3.10
    from collections.abc import Iterable

from contextlib import contextmanager
from typing import Union

from lumigo_opentelemetry import logger


@contextmanager
def lumigo_safe_execute(part_name=""):
    try:
        yield
    except Exception as e:
        logger.exception(
            f"An exception occurred in lumigo's code {part_name}", exc_info=e
        )


def safe_split_get(string: str, sep: str, index: int, default=None) -> str:
    """
    This function splits the given string using the sep, and returns the organ in the `index` place.
    If such index doesn't exist, returns default.
    """
    if not isinstance(string, str):
        return default
    return safe_get_list(string.split(sep), index, default)


def safe_get_list(lst: list, index: Union[int, str], default=None):
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
