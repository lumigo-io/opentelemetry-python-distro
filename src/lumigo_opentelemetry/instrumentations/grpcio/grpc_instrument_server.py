from typing import List, Any

from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from opentelemetry.trace import get_current_span
from grpc._utilities import RpcMethodHandler
from grpc._server import _RequestIterator

from .config import PAYLOAD_MAX_SIZE


def request_wrapper(request: _RequestIterator) -> None:
    history: List[str] = []
    original_next = request._next

    def wrapped_next() -> Any:
        data_chunk = original_next()
        if len(str(history)) < PAYLOAD_MAX_SIZE:
            history.append(str(data_chunk))
            get_current_span().set_attribute(
                "rpc.request.payload", ",".join(history)[:PAYLOAD_MAX_SIZE]
            )
        return data_chunk

    request._next = wrapped_next


class LumigoServerInterceptor(OpenTelemetryServerInterceptor):
    def _start_span(self, handler_call_details, context, set_status_on_exception=False):  # type: ignore
        ctx = super()._start_span(
            handler_call_details,
            context,
            set_status_on_exception=set_status_on_exception,
        )
        if getattr(self, "latest_request", None) is not None:
            if isinstance(self.latest_request, _RequestIterator):
                request_wrapper(self.latest_request)
            else:
                ctx.kwds["attributes"]["rpc.request.payload"] = str(
                    self.latest_request
                )[:PAYLOAD_MAX_SIZE]
        return ctx

    def intercept_service(self, continuation, handler_call_details):  # type: ignore
        original = super().intercept_service(continuation, handler_call_details)

        def wrapper(func):  # type: ignore
            def wrapped(request_or_iterator, context):  # type: ignore
                self.latest_request = request_or_iterator
                return func(request_or_iterator, context)

            return wrapped

        return RpcMethodHandler(
            request_streaming=original.request_streaming,
            response_streaming=original.response_streaming,
            request_deserializer=original.request_deserializer,
            response_serializer=original.response_serializer,
            unary_unary=wrapper(original.unary_unary),
            unary_stream=wrapper(original.unary_stream),
            stream_unary=wrapper(original.stream_unary),
            stream_stream=wrapper(original.stream_stream),
        )

    def _intercept_server_stream(  # type: ignore
        self, behavior, handler_call_details, request_or_iterator, context
    ):
        self.latest_request = request_or_iterator
        return super()._intercept_server_stream(
            behavior, handler_call_details, request_or_iterator, context
        )
