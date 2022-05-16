from typing import Any


class Flask:
    @staticmethod
    def is_flask(resource: Any) -> bool:
        try:
            import flask

            return isinstance(resource, flask.Flask)
        except ImportError:
            return False

    @staticmethod
    def instrument(resource: Any):
        if Flask.is_flask(resource=resource):
            try:
                from opentelemetry.instrumentation.flask import FlaskInstrumentor

                FlaskInstrumentor().instrument_app(resource)
            except ImportError:
                pass
