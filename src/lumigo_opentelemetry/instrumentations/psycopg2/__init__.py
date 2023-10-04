import wrapt
from opentelemetry.trace import SpanKind
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.libs.json_utils import dump_with_context
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute


class Psycopg2Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("psycopg2")

    def check_if_applicable(self) -> None:
        import psycopg2  # noqa

    def install_instrumentation(self) -> None:

        from opentelemetry.instrumentation import psycopg2
        from opentelemetry.instrumentation.dbapi import DatabaseApiIntegration

        # Patch the connect function to capture parameters (db.statement.parameters)
        def new_wrap_connect(original_func, instance, args, kwargs):  # type: ignore
            kwargs["capture_parameters"] = True
            return original_func(*args, **kwargs)

        # Patch the _new_cursor_factory function to capture all the responses from all the fetch functions
        def patched__new_cursor_factory(original_func, instance, args, kwargs):  # type: ignore
            db_api = kwargs["db_api"]
            _cursor_tracer = psycopg2.CursorTracer(db_api)
            original_response = original_func(*args, **kwargs)
            # Patch all the fetch functions in `psycopg2.extensions.cursor`
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

        wrapt.wrap_function_wrapper(
            DatabaseApiIntegration, "__init__", new_wrap_connect
        )
        wrapt.wrap_function_wrapper(
            psycopg2, "_new_cursor_factory", patched__new_cursor_factory
        )

        # if we don't skip the dependency check, the instrumentor will fail
        # because it can't detect psycopg2-binary
        psycopg2.Psycopg2Instrumentor().instrument(skip_dep_check=True)


instrumentor: AbstractInstrumentor = Psycopg2Instrumentor()
