from collections.abc import Iterator
from typing import Any, Iterator as IteratorType

from opentelemetry.instrumentation.grpc._client import OpenTelemetryClientInterceptor

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.instrumentations.instrumentation_utils import PAYLOAD_MAX_SIZE

from .common import add_payload_in_bulks


def iterator_wrapper(
    iterator: IteratorType[Any], attribute_name: str
) -> IteratorType[Any]:
    add_payload = add_payload_in_bulks(attribute_name)

    for data_chunk in iterator:
        add_payload(data_chunk)
        yield data_chunk


class LumigoClientInterceptor(OpenTelemetryClientInterceptor):
    def _start_span(self, method, **kwargs):  # type: ignore
        ctx = super()._start_span(method, **kwargs)
        with lumigo_safe_execute("LumigoClientInterceptor._start_span"):
            if getattr(self, "latest_request", None) is not None:
                # if it's an iterator, we already set the attribute in the iterator wrapper
                if not isinstance(self.latest_request, Iterator):
                    ctx.kwds["attributes"]["rpc.grpc.request.payload"] = str(
                        self.latest_request
                    )[:PAYLOAD_MAX_SIZE]
        return ctx

    def _intercept(self, request, metadata, client_info, invoker):  # type: ignore
        if isinstance(request, Iterator):
            request = iterator_wrapper(request, "rpc.grpc.request.payload")
        else:
            self.latest_request = request
        return super()._intercept(request, metadata, client_info, invoker)

    def _intercept_server_stream(  # type: ignore
        self, request_or_iterator, metadata, client_info, invoker
    ):
        """
        This is a wrapper to the original _intercept_server_stream method.
        The flow is:
        1. Get the payload from the request
            a. Iterator - we wrap the iterator with the iterator wrapper
            b. Non-iterator - we save the request in the latest_request member
        2. call the original method
        3. wrap the response with the iterator wrapper (to read the payload)
        """
        if isinstance(request_or_iterator, Iterator):
            request_or_iterator = iterator_wrapper(
                request_or_iterator, "rpc.grpc.request.payload"
            )
        else:
            self.latest_request = request_or_iterator
        result = super()._intercept_server_stream(
            request_or_iterator, metadata, client_info, invoker
        )
        return iterator_wrapper(result, "rpc.grpc.response.payload")

    def _trace_result(self, span, rpc_info, result):  # type: ignore
        span.set_attribute("rpc.grpc.response.payload", str(result)[:PAYLOAD_MAX_SIZE])
        return super()._trace_result(span, rpc_info, result)
