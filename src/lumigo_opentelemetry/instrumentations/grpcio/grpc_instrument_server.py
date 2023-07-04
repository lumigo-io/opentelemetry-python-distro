from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from grpc._utilities import RpcMethodHandler


class LumigoServerInterceptor(OpenTelemetryServerInterceptor):
    def _start_span(self, handler_call_details, context, set_status_on_exception=False):  # type: ignore
        ctx = super()._start_span(
            handler_call_details,
            context,
            set_status_on_exception=set_status_on_exception,
        )
        if getattr(self, "latest_request", None) is not None:
            ctx.kwds["attributes"]["rpc.payload"] = str(self.latest_request)
        return ctx

    def intercept_service(self, continuation, handler_call_details):  # type: ignore
        original = super().intercept_service(continuation, handler_call_details)

        def wrapped(request_or_iterator, context):  # type: ignore
            self.latest_request = request_or_iterator
            return original.unary_unary(request_or_iterator, context)

        return RpcMethodHandler(
            request_streaming=original.request_streaming,
            response_streaming=original.response_streaming,
            request_deserializer=original.request_deserializer,
            response_serializer=original.response_serializer,
            unary_unary=wrapped,
            unary_stream=original.unary_stream,
            stream_unary=original.stream_unary,
            stream_stream=original.stream_stream,
        )
