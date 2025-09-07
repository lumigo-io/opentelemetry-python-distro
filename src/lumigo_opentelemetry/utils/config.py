import os
from typing import Set

_DEFAULT_CONNECTION_TIMEOUT = 3


def get_connection_timeout_seconds() -> float:
    return float(
        os.environ.get("LUMIGO_CONNECTION_TIMEOUT", _DEFAULT_CONNECTION_TIMEOUT)
    )


def get_disabled_instrumentations() -> Set[str]:
    """
    Parse the LUMIGO_DISABLE_INSTRUMENTATION environment variable.

    Returns a set of instrumentation names that should be disabled.
    The environment variable should contain a comma-separated list of instrumentation names.

    Example: LUMIGO_DISABLE_INSTRUMENTATION="boto,requests,redis"
    """
    disabled_env = os.environ.get("LUMIGO_DISABLE_INSTRUMENTATION", "")
    if not disabled_env:
        return set()

    # Split by comma, strip whitespace, and filter out empty strings
    disabled_list = [name.strip() for name in disabled_env.split(",") if name.strip()]
    return set(disabled_list)
