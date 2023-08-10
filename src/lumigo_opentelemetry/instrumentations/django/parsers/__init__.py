from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.json_utils import dump_with_context


class DjangoUtil:
    @staticmethod
    def request_hook(span, request):
        try:
            attributes = {
                "http.request.body": dump_with_context("requestBody", request.body),
                "http.request.headers": dump_with_context(
                    "requestHeaders", request.headers
                ),
            }
            span.set_attributes(attributes)
        except Exception as err:
            logger.exception("failed extracting django request", exc_info=err)

    @staticmethod
    def response_hook(span, request, response):
        try:
            attributes = {
                "http.response.body": dump_with_context("responseBody", response.text),
                "http.response.headers": dump_with_context(
                    "responseHeaders", response.headers
                ),
                "http.request.body": dump_with_context("requestBody", request.body),
                "http.request.headers": dump_with_context(
                    "requestHeaders", request.headers
                ),
            }
            span.set_attributes(attributes)
        except Exception as err:
            logger.exception("failed extracting django response", exc_info=err)
