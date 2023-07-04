from opentelemetry.instrumentation.grpc._client import OpenTelemetryClientInterceptor


class LumigoClientInterceptor(OpenTelemetryClientInterceptor):
    def _start_span(self, method, **kwargs):  # type: ignore
        ctx = super()._start_span(method, **kwargs)
        if getattr(self, "latest_request", None) is not None:
            ctx.kwds["attributes"]["rpc.payload"] = str(self.latest_request)
        return ctx

    def _intercept(self, request, metadata, client_info, invoker):  # type: ignore
        self.latest_request = request
        return super()._intercept(request, metadata, client_info, invoker)

    def _intercept_server_stream(  # type: ignore
        self, request_or_iterator, metadata, client_info, invoker
    ):
        self.latest_request = request_or_iterator
        return super()._intercept_server_stream(
            request_or_iterator, metadata, client_info, invoker
        )
