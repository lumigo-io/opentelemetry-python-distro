import unittest

from test.test_utils.spans_parser import SpansContainer


class TestBoto3SqsSpans(unittest.TestCase):
    def test_boto3_instrumentation(self):
        spans_container = SpansContainer.parse_spans_from_file()
        self.assertEqual(12, len(spans_container.spans))

        [
            create_queue_span,
            send_message_1_span,
            send_message_2_span,
            send_message_3_span,
            receive_message_1_span,
            # The unintuitive ordering of the unpacking is due to the fact
            # that the child nested at level 2 is ended first
            consume_message_2_span,
            consume_message_1_span,
            iterator_on_copy_span,
            processing_message_2_span,
            processing_message_3_span,
            receive_message_2_span,
            after_iterator_break_span,
        ] = spans_container.spans

        self.assertEqual(create_queue_span["name"], "SQS.CreateQueue")
        self.assertIsNone(create_queue_span["parent_id"])

        self.assertEqual(send_message_1_span["name"], "SQS.SendMessage")
        self.assertIsNone(send_message_1_span["parent_id"])

        self.assertEqual(send_message_2_span["name"], "SQS.SendMessage")
        self.assertIsNone(send_message_2_span["parent_id"])

        self.assertEqual(send_message_3_span["name"], "SQS.SendMessage")
        self.assertIsNone(send_message_3_span["parent_id"])

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

        self.assertNotEquals(
            receive_message_2_span["context"]["trace_id"],
            receive_message_1_span["context"]["trace_id"],
        )
        self.assertEqual(receive_message_2_span["name"], "SQS.ReceiveMessage")
        self.assertIsNone(receive_message_2_span["parent_id"])

        self.assertEqual(iterator_on_copy_span["name"], "iterator_on_copy")
        self.assertIsNone(iterator_on_copy_span["parent_id"])
        self.assertNotEquals(
            iterator_on_copy_span["context"]["trace_id"],
            receive_message_2_span["context"]["trace_id"],
        )

        self.assertTrue(processing_message_2_span["name"].startswith("Message "))
        self.assertEqual(
            processing_message_2_span["context"]["trace_id"],
            receive_message_2_span["context"]["trace_id"],
        )
        self.assertEqual(
            processing_message_2_span["parent_id"],
            receive_message_2_span["context"]["span_id"],
        )
        self.assertListEqual(
            processing_message_2_span["links"],
            [
                {
                    "context": {
                        "trace_id": send_message_2_span["context"]["trace_id"],
                        "span_id": send_message_2_span["context"]["span_id"],
                        "trace_state": "[]",
                    },
                    "attributes": {
                        "messaging.message_id": send_message_2_span["attributes"][
                            "messaging.message_id"
                        ]
                    },
                }
            ],
        )

        self.assertTrue(processing_message_3_span["name"].startswith("Message "))
        self.assertEqual(
            processing_message_3_span["context"]["trace_id"],
            receive_message_2_span["context"]["trace_id"],
        )
        self.assertEqual(
            processing_message_3_span["parent_id"],
            receive_message_2_span["context"]["span_id"],
        )
        self.assertListEqual(
            processing_message_3_span["links"],
            [
                {
                    "context": {
                        "trace_id": send_message_3_span["context"]["trace_id"],
                        "span_id": send_message_3_span["context"]["span_id"],
                        "trace_state": "[]",
                    },
                    "attributes": {
                        "messaging.message_id": send_message_3_span["attributes"][
                            "messaging.message_id"
                        ]
                    },
                }
            ],
        )

        self.assertEqual(after_iterator_break_span["name"], "after_iterator_break")
        self.assertIsNone(after_iterator_break_span["parent_id"])
        self.assertNotEquals(
            after_iterator_break_span["context"]["trace_id"],
            iterator_on_copy_span["context"]["trace_id"],
        )
