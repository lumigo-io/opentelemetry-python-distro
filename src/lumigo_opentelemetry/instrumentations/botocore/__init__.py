from typing import Dict, Any

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.resources.span_processor import set_span_skip_export
from opentelemetry.trace import Span, SpanKind

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.botocore.parsers import AwsParser
from lumigo_opentelemetry.libs.sampling import should_sample
from lumigo_opentelemetry.utils.span_utils import safe_get_span_attributes


class BotoCoreInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("botocore")

    def check_if_applicable(self) -> None:
        from botocore.client import BaseClient  # noqa
        from botocore.endpoint import Endpoint  # noqa
        from botocore.exceptions import ClientError  # noqa

    def install_instrumentation(self) -> None:
        # We're using a copied version of this instrumentor until this PR will be merged:
        # https://github.com/open-telemetry/opentelemetry-python-contrib/pull/1350
        # After the merge, delete the following line and uncomment the next line
        from lumigo_opentelemetry.external.botocore import BotocoreInstrumentor

        # from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

        BotocoreInstrumentor().instrument(
            request_hook=AwsParser.request_hook,
            response_hook=filtered_resource_hook,
        )


def filtered_resource_hook(
    span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
) -> None:
    AwsParser.response_hook(span, service_name, operation_name, result)
    with lumigo_safe_execute("aws: response_hook skip check"):
        span_attributes = safe_get_span_attributes(span)
        if span_attributes:
            if not should_sample(span_attributes, SpanKind.CLIENT):
                set_span_skip_export(span)


instrumentor: AbstractInstrumentor = BotoCoreInstrumentorWrapper()
