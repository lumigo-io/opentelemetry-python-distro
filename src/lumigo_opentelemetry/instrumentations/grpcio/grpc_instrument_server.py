from typing import Any

from grpc._utilities import RpcMethodHandler
from grpc._server import _RequestIterator
from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.instrumentations.instrumentation_utils import PAYLOAD_MAX_SIZE

from .common import add_payload_in_bulks


def request_wrapper(request: _RequestIterator) -> None:
    add_payload = add_payload_in_bulks("rpc.grpc.request.payload")
    original_next = request._next

    def wrapped_next() -> Any:
        data_chunk = original_next()
        add_payload(data_chunk)
        return data_chunk

    request._next = wrapped_next


class LumigoServerInterceptor(OpenTelemetryServerInterceptor):
    def _start_span(self, handler_call_details, context, set_status_on_exception=False):  # type: ignore
        ctx = super()._start_span(
            handler_call_details,
            context,
            set_status_on_exception=set_status_on_exception,
        )
        with lumigo_safe_execute("LumigoServerInterceptor._start_span"):
            if getattr(self, "latest_request", None) is not None:
                if isinstance(self.latest_request, _RequestIterator):
                    request_wrapper(self.latest_request)
                else:
                    ctx.kwds["attributes"]["rpc.grpc.request.payload"] = str(
                        self.latest_request
                    )[:PAYLOAD_MAX_SIZE]
        return ctx

    def intercept_service(self, continuation, handler_call_details):  # type: ignore
        original = super().intercept_service(continuation, handler_call_details)

        with lumigo_safe_execute("LumigoServerInterceptor.intercept_service"):

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
        return original

    def _intercept_server_stream(  # type: ignore
        self, behavior, handler_call_details, request_or_iterator, context
    ):
        self.latest_request = request_or_iterator
        return super()._intercept_server_stream(
            behavior, handler_call_details, request_or_iterator, context
        )
