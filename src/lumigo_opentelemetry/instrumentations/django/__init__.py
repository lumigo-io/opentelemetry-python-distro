from opentelemetry.trace.span import Span

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)
from lumigo_opentelemetry.libs.environment_variables import (
    AUTO_FILTER_HTTP_ENDPOINTS_REGEX,
)
from lumigo_opentelemetry.libs.general_utils import (
    lumigo_safe_execute,
    should_skip_span_on_route_match,
)
from lumigo_opentelemetry.libs.json_utils import dump_with_context
from lumigo_opentelemetry.resources.span_processor import set_span_skip_export


class DjangoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("django")

    def check_if_applicable(self) -> None:
        import django  # noqa

    def install_instrumentation(self) -> None:
        from django.http import HttpRequest, HttpResponse
        from opentelemetry.instrumentation.django import DjangoInstrumentor

        def request_hook(span: Span, request: HttpRequest) -> None:
            with lumigo_safe_execute("django request_hook"):
                span.set_attribute(
                    "http.request.headers",
                    dump_with_context("requestHeaders", request.headers),
                )
                add_body_attribute(span, request.body, "http.request.body")

                request_url = request.build_absolute_uri()
                if should_skip_span_on_route_match(request_url):
                    logger.info(
                        f"Not tracing url '{request_url}' because it matches the auto-filter"
                        f" regex specified by '{AUTO_FILTER_HTTP_ENDPOINTS_REGEX}'"
                    )
                    set_span_skip_export(span)

        def response_hook(
            span: Span, request: HttpRequest, response: HttpResponse
        ) -> None:
            with lumigo_safe_execute("django response_hook"):
                span.set_attribute(
                    "http.response.headers",
                    dump_with_context("responseHeaders", response.headers),
                )
                add_body_attribute(span, response.content, "http.response.body")

        DjangoInstrumentor().instrument(
            request_hook=request_hook, response_hook=response_hook
        )


instrumentor: AbstractInstrumentor = DjangoInstrumentorWrapper()
