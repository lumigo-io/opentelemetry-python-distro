import json
from decimal import Decimal
from typing import Any

from lumigo_wrapper.lumigo_utils import get_logger


def dump(to_dump: Any) -> str:
    try:
        return json.dumps(to_dump)
    except Exception:
        try:
            return str(to_dump)
        except Exception as e:
            get_logger().exception("failed to dump object", exc_info=e)
            pass
    return ""


def aws_dump(d: Any, decimal_safe=False, **kwargs) -> str:
    if decimal_safe:
        return json.dumps(d, cls=DecimalEncoder, **kwargs)
    return json.dumps(d, **kwargs)


class DecimalEncoder(json.JSONEncoder):
    # copied from python's runtime: runtime/lambda_runtime_marshaller.py:7-11
    def default(self, o):
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
