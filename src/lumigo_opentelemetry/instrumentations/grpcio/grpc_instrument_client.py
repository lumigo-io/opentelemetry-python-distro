from collections.abc import Iterator
from typing import List, Any, Iterator as IteratorType

from opentelemetry.trace import get_current_span
from opentelemetry.instrumentation.grpc._client import OpenTelemetryClientInterceptor

from .config import PAYLOAD_MAX_SIZE


def iterator_wrapper(it: IteratorType[Any], attribute_name: str) -> IteratorType[Any]:
    history: List[str] = []
    for data_chunk in it:
        if len(str(history)) < PAYLOAD_MAX_SIZE:
            history.append(str(data_chunk))
            get_current_span().set_attribute(attribute_name, ",".join(history)[:PAYLOAD_MAX_SIZE])
        yield data_chunk


class LumigoClientInterceptor(OpenTelemetryClientInterceptor):
    def _start_span(self, method, **kwargs):  # type: ignore
        ctx = super()._start_span(method, **kwargs)
        if getattr(self, "latest_request", None) is not None:
            if not isinstance(self.latest_request, Iterator):
                ctx.kwds["attributes"]["rpc.request.payload"] = str(self.latest_request)[:PAYLOAD_MAX_SIZE]
        return ctx

    def _intercept(self, request, metadata, client_info, invoker):  # type: ignore
        if isinstance(request, Iterator):
            request = iterator_wrapper(request, "rpc.request.payload")
        else:
            self.latest_request = request
        return super()._intercept(request, metadata, client_info, invoker)

    def _intercept_server_stream(  # type: ignore
        self, request_or_iterator, metadata, client_info, invoker
    ):
        if isinstance(request_or_iterator, Iterator):
            request_or_iterator = iterator_wrapper(
                request_or_iterator, "rpc.request.payload"
            )
        else:
            self.latest_request = request_or_iterator
        result = super()._intercept_server_stream(
            request_or_iterator, metadata, client_info, invoker
        )
        return iterator_wrapper(result, "rpc.response.payload")

    def _trace_result(self, span, rpc_info, result):  # type: ignore
        span.set_attribute("rpc.response.payload", str(result)[:PAYLOAD_MAX_SIZE])
        return super()._trace_result(span, rpc_info, result)
