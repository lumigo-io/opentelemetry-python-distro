# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from lumigo_opentelemetry.external.botocore.extensions.types import (
    _AttributeMapT,
    _AwsSdkExtension,
    _BotoResultT,
)
from opentelemetry import context as context_api
from opentelemetry.propagate import extract, inject
from opentelemetry.propagators.textmap import CarrierT, Getter, Setter
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import get_current_span, get_tracer, Link, set_span_in_context
from opentelemetry.trace.propagation import _SPAN_KEY
from opentelemetry.trace.span import NonRecordingSpan, Span
from typing import Any, Generator


_SUPPORTED_OPERATIONS = ["SendMessage", "SendMessageBatch", "ReceiveMessage"]


class _SqsExtension(_AwsSdkExtension):

    def extract_attributes(self, attributes: _AttributeMapT):
        queue_url = self._call_context.params.get("QueueUrl")
        if queue_url:
            # TODO: update when semantic conventions exist
            attributes["aws.queue_url"] = queue_url
            attributes[SpanAttributes.MESSAGING_SYSTEM] = "aws.sqs"
            attributes[SpanAttributes.MESSAGING_URL] = queue_url
            attributes[SpanAttributes.MESSAGING_DESTINATION] = queue_url.split(
                "/"
            )[-1]

    def before_service_call(self, span: Span):
        operation = self._call_context.operation
        params = self._call_context.params

        if operation == "SendMessage":
            if "MessageAttributes" not in params:
                params["MessageAttributes"] = {}

            inject(
                params["MessageAttributes"],
                context_api.get_current(),
                _SqsExtension.SqsMetadataContextSetter(),
            )

        elif operation == "SendMessageBatch":
            for entry in params["Entries"]:
                params["MessageAttributes"] = {}

                inject(
                    entry["MessageAttributes"],
                    context_api.get_current(),
                    _SqsExtension.SqsMetadataContextSetter(),
                )

        elif operation == "ReceiveMessage":
            params = self._call_context.params

            if "MessageAttributeNames" not in params:
                params["MessageAttributeNames"] = []

            # TODO find expected headers based on propagator
            params["MessageAttributeNames"].append("traceparent")

    def on_success(self, span: Span, result: _BotoResultT):
        operation = self._call_context.operation
        if operation in _SUPPORTED_OPERATIONS:
            if operation == "SendMessage":
                span.set_attribute(
                    SpanAttributes.MESSAGING_MESSAGE_ID,
                    result.get("MessageId"),
                )

            elif operation == "SendMessageBatch" and result.get("Successful"):
                span.set_attribute(
                    SpanAttributes.MESSAGING_MESSAGE_ID,
                    result["Successful"][0]["MessageId"],
                )
            elif operation == "ReceiveMessage" and result.get("Messages"):
                messages = result["Messages"]

                span.set_attribute(
                    SpanAttributes.MESSAGING_MESSAGE_ID,
                    messages[0]["MessageId"],
                )

                # Replace the 'Messages' list with a list that restores `span` as trace
                # context over iterations.
                ctx = _SqsExtension.ScopeContext(span)

                if len(messages) > 1:
                    # TODO Change this to something sensible?
                    tracer = get_tracer(__name__)
                    now = time.time()

                    for message in messages:
                        message_id = message["MessageId"]
                        links = []
                        if "MessageAttributes" in message and "traceparent" in message["MessageAttributes"]:
                            # This apparently is the "best" way to go from context to the span inside
                            # without attaching the context...
                            for item in extract(message["MessageAttributes"], getter=_SqsExtension.SqsMetadataContextGetter()).values():
                                if isinstance(item, Span):
                                    links.append(Link(context=item.get_span_context(), attributes={
                                        SpanAttributes.MESSAGING_MESSAGE_ID: message_id,
                                    }))

                        context = set_span_in_context(span)
                        tracer.start_span(
                            f"Message {message_id}",
                            context=context,
                            attributes={SpanAttributes.MESSAGING_MESSAGE_ID: message_id},
                            links=links,
                            start_time=now
                        ).end(now)

                result["Messages"] = _SqsExtension.ContextableList(result["Messages"], ctx)


    class ScopeContext:
        def __init__(self, span: Span):
            self._span = span
            self._scope_depth = 0
            self._token = None

        def _enter(self):
            # NonRecordingSpan is what we get when there is no span in the context
            if self._scope_depth == 0 and isinstance(get_current_span(), NonRecordingSpan):
                # If there is not current active span (e.g. in case of an overarching entry span),
                # we restore as active the "ReceiveMessage" span. We neither record exceptions on it
                # nor set statuses, as the "ReceiveMessage" span is already ended when it is used as
                # parent by spans created while iterating on the messages.
                self._token = context_api.attach(context_api.set_value(_SPAN_KEY, self._span))
                self._scope_depth = 1
            else:
                self._scope_depth = self._scope_depth + 1

        def _exit(self):
            if not self._scope_depth:
                # Something very fishy going on!
                return

            self._scope_depth = self._scope_depth - 1

            if self._scope_depth == 0 and self._token:
                # Clear the context outside of the iteration, so that a second iteration would
                # revert to the previous context
                context_api.detach(self._token)
                self._token = None

    class ContextableList(list):
        """
        Since the classic way to process SQS messages is using a `for` loop, without a well defined scope like a
        callback - we are doing something similar to the instrumentation of Kafka-python and instrumenting the
        `__iter__` functions and the `__getitem__` functions to set the span context of the "ReceiveMessage" span.

        Since the return value from an `SQS.ReceiveMessage` returns a builtin list, we cannot wrap it and change
        all of the calls for `list.__iter__` and `list.__getitem__` - therefore we use ContextableList.

        This object also implements the `__enter__` and `__exit__` objects for context managers.
        """
        def __init__(self, l, scopeContext):
            super().__init__(l)
            self._scopeContext = scopeContext

        # Iterator support
        def __iter__(self) -> Generator:
            # Try / finally ensures that we detach the context over a `break` issues from inside an iteration
            try:
                self._scopeContext._enter()

                index = 0
                while index < len(self):
                    yield self[index]
                    index = index + 1
            finally:
                self._scopeContext._exit()


    class SqsMetadataContextSetter(Setter):

        def set(self, message_attributes: CarrierT, key: str, value: Any):  # pylint: disable=no-self-use
            message_attributes[key] = {
                "StringValue": str(value),
                "DataType": "String",
            }


    class SqsMetadataContextGetter(Getter):

        def get(self, message_attributes: CarrierT, key: str):
            if key in message_attributes:
                if val := message_attributes[key]:
                    # TODO Implement other datatypes?
                    if "DataType" in val and val["DataType"] == "String":
                        return [str(val["StringValue"])]

        def keys(self, message_attributes: CarrierT):
            return message_attributes.keys()