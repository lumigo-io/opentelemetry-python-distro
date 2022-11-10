import os

_DEFAULT_CONNECTION_TIMEOUT = 3


def get_connection_timeout_seconds() -> float:
    return float(
        os.environ.get("LUMIGO_CONNECTION_TIMEOUT", _DEFAULT_CONNECTION_TIMEOUT)
    )
