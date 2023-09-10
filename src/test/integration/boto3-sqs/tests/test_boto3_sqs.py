import unittest
from test.test_utils.spans_parser import SpansContainer


class TestBoto3SqsSpans(unittest.TestCase):
    def test_boto3_instrumentation(self):
        spans_container = SpansContainer.parse_spans_from_file()
        self.assertEqual(12, len(spans_container.spans))

        [
            create_queue_span,
            empty_sqs_poll_1_span,
            empty_sqs_poll_2_span,
            empty_sqs_poll_3_span,
            send_message_1_span,
            send_message_2_span,
            receive_message_1_span,
            # The unintuitive ordering of the unpacking is due to the fact
            # that the child nested at level 2 is ended first
            consume_message_2_span,
            consume_message_1_span,
            iterator_on_copy_span,
            receive_message_2_span,
            after_iterator_break_span,
        ] = spans_container.spans

        # Make sure that all the empty polling spans are marked as skipped
        for span in [empty_sqs_poll_1_span, empty_sqs_poll_2_span, empty_sqs_poll_3_span]:
            self.assertIsNotNone(span.get("attributes"))
            self.assertEqual(span["attributes"].get("SKIP_EXPORT"), True)

        # Make sure that other spans are not marked as skipped
        for span in [create_queue_span,
                     send_message_1_span,
                     send_message_2_span,
                     receive_message_1_span,
                     receive_message_2_span,
                     consume_message_2_span,
                     consume_message_1_span,
                     receive_message_2_span]:
            self.assertNotEqual(span.get("attributes", {}).get("SKIP_EXPORT"), True)

        self.assertEqual(create_queue_span["name"], "SQS.CreateQueue")
        self.assertIsNone(create_queue_span["parent_id"])

        self.assertEqual(send_message_1_span["name"], "SQS.SendMessage")
        self.assertIsNone(send_message_1_span["parent_id"])

        self.assertEqual(send_message_2_span["name"], "SQS.SendMessage")
        self.assertIsNone(send_message_2_span["parent_id"])

        self.assertEqual(receive_message_1_span["name"], "SQS.ReceiveMessage")
        self.assertIsNone(receive_message_1_span["parent_id"])

        self.assertEqual(consume_message_1_span["name"], "consuming_message_1")
        self.assertEqual(
            consume_message_1_span["context"]["trace_id"],
            receive_message_1_span["context"]["trace_id"],
        )
        self.assertEqual(
            consume_message_1_span["parent_id"],
            receive_message_1_span["context"]["span_id"],
        )

        self.assertEqual(consume_message_2_span["name"], "consuming_message_2")
        self.assertEqual(
            consume_message_2_span["context"]["trace_id"],
            receive_message_1_span["context"]["trace_id"],
        )
        self.assertEqual(
            consume_message_2_span["parent_id"],
            consume_message_1_span["context"]["span_id"],
        )

        self.assertNotEqual(
            receive_message_2_span["context"]["trace_id"],
            receive_message_1_span["context"]["trace_id"],
        )
        self.assertEqual(receive_message_2_span["name"], "SQS.ReceiveMessage")
        self.assertIsNone(receive_message_2_span["parent_id"])

        self.assertEqual(iterator_on_copy_span["name"], "iterator_on_copy")
        self.assertIsNone(iterator_on_copy_span["parent_id"])
        self.assertNotEqual(
            iterator_on_copy_span["context"]["trace_id"],
            receive_message_2_span["context"]["trace_id"],
        )

        self.assertEqual(after_iterator_break_span["name"], "after_iterator_break")
        self.assertIsNone(after_iterator_break_span["parent_id"])
        self.assertNotEqual(
            after_iterator_break_span["context"]["trace_id"],
            iterator_on_copy_span["context"]["trace_id"],
        )
