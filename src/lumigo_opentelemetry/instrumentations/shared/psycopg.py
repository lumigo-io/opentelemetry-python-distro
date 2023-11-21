from typing import Any

import wrapt
from opentelemetry.instrumentation.dbapi import DatabaseApiIntegration
from opentelemetry.trace import SpanKind

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump_with_context


def patch_psycopg_for_payload_capture(package: Any) -> None:
    # Patch the connect function to capture parameters (db.statement.parameters)
    def new_wrap_connect(original_func, instance, args, kwargs):  # type: ignore
        kwargs["capture_parameters"] = True
        return original_func(*args, **kwargs)

    # Patch the _new_cursor_factory function to capture all the responses from all the fetch functions
    def patched__new_cursor_factory(original_func, instance, args, kwargs):  # type: ignore
        db_api = kwargs["db_api"]
        _cursor_tracer = package.CursorTracer(db_api)
        original_response = original_func(*args, **kwargs)
        # Patch all the fetch functions (`psycopg.Cursor` and `psycopg2.extensions.cursor`)
        original_functions = {
            fetch_function: getattr(original_response, fetch_function)
            for fetch_function in ["fetchone", "fetchmany", "fetchall"]
        }
        for (
            fetch_function_name,
            original_fetch_function,
        ) in original_functions.items():

            def wrapper(  # type: ignore
                fetch_function_name: str, original_fetch_function
            ):
                def func(self, *args, **kwargs):  # type: ignore
                    with db_api._tracer.start_as_current_span(
                        fetch_function_name, kind=SpanKind.CLIENT
                    ) as span:
                        result = original_fetch_function(self, *args, **kwargs)
                        with lumigo_safe_execute(
                            f"set response body ({fetch_function_name})"
                        ):
                            _cursor_tracer._populate_span(span, None, *args)
                            span.set_attribute(
                                "db.response.body",
                                dump_with_context("responseBody", result),
                            )
                    return result

                return func

            setattr(
                original_response,
                fetch_function_name,
                wrapper(fetch_function_name, original_fetch_function),
            )
        return original_response

    wrapt.wrap_function_wrapper(DatabaseApiIntegration, "__init__", new_wrap_connect)
    wrapt.wrap_function_wrapper(
        package, "_new_cursor_factory", patched__new_cursor_factory
    )
