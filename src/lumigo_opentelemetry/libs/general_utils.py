import functools
import logging

try:
    from collections import Iterable
except ImportError:
    # collections.Iterables was removed in Python 3.10
    from collections.abc import Iterable

import os
from contextlib import contextmanager
from typing import Generator, List, Optional, TypeVar, Union, Any, Callable, cast

from opentelemetry.sdk.environment_variables import (
    OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT,
    OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT,
)

from lumigo_opentelemetry import logger

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


TCallable = TypeVar("TCallable", bound=Callable)  # type: ignore


def lumigo_safe_wrapper(
    default_return_value: Any = None, level: Optional[int] = logging.ERROR
) -> Callable:  # type: ignore
    """
    A wrapper to safely execute a function, and return a default value in case of an exception.
    @param default_return_value:
    @param level: The log level for the error message. If None, no error message will be logged.
    @return: The wrapper function
    """

    def decorator(func: TCallable) -> TCallable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if level is not None:
                    logger.log(
                        level=level,
                        msg=f"An exception occurred in lumigo's code {func.__name__}",
                        exc_info=e,
                    )

            return default_return_value

        return cast(TCallable, wrapper)

    return decorator


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


def get_boolean_env_var(env_var_name: str, default: bool = False) -> bool:
    """
    This function return the boolean value of the given environment variable.
    If this values doesn't exist, return default.

    @param env_var_name: The env var to get (case-sensitive)
    @param default: Default value if env var is not set
    @return: The boolean value of the env var
    """

    env_var_value = os.environ.get(env_var_name, str(default))
    env_var_value = (
        env_var_value.lower() if isinstance(env_var_value, str) else env_var_value
    )

    is_truth_value = env_var_value == "true"
    is_false_value = env_var_value == "false"
    if not is_truth_value and not is_false_value:
        logger.debug(
            f'Invalid boolean value for env var "{env_var_name}", '
            f'defaulting to value "{str(default).lower()}"'
        )
        return default

    return is_truth_value
