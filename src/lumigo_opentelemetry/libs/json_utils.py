from typing import Any, Optional, List

from lumigo_opentelemetry.libs.general_utils import get_max_size
from lumigo_core.scrubbing import lumigo_dumps, lumigo_dumps_with_context


def dump(
    to_dump: Any,
    decimal_safe: bool = False,
    omit_skip_path: Optional[List[str]] = None,
    max_size: Optional[int] = None,
    enforce_jsonify: bool = False,
) -> str:
    return lumigo_dumps(  # type: ignore
        d=to_dump,
        max_size=max_size or get_max_size(),
        decimal_safe=decimal_safe,
        omit_skip_path=omit_skip_path,
        enforce_jsonify=enforce_jsonify,
    )


def dump_with_context(
    context: str,
    to_dump: Any,
) -> str:
    return lumigo_dumps_with_context(  # type: ignore
        context=context,
        d=to_dump,
        max_size=get_max_size(),
    )


def safe_convert_bytes_to_string(value: Any) -> Any:
    try:
        return value.decode("utf-8")
    except Exception:
        return value
