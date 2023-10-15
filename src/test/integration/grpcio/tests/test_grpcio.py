import os
import sys
import unittest

from .app_runner import GreeterServerApp

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from test.test_utils.spans_parser import SpansContainer  # noqa: E402

import grpc  # noqa: E402
import helloworld_pb2  # noqa: E402
import helloworld_pb2_grpc  # noqa: E402


class TestGrpcioSpans(unittest.TestCase):
    def check_spans(self, method: str, request_payload: str, response_payload: str):
        server_spans = SpansContainer.get_spans_from_file(
            path=os.environ["SERVER_SPANDUMP"], wait_time_sec=10, expected_span_count=1
        )
        assert len(server_spans.spans) == 1

        server_span = server_spans.spans[0]
        assert server_span["kind"] == "SpanKind.SERVER"
        assert server_span["attributes"]["rpc.method"] == method
        assert server_span["attributes"]["rpc.service"] == "helloworld.Greeter"
        assert server_span["attributes"]["rpc.system"] == "grpc"

        client_spans = SpansContainer.get_spans_from_file(
            wait_time_sec=10, expected_span_count=1
        )
        assert len(client_spans.spans) == 1

        client_span = client_spans.spans[0]
        assert client_span["kind"] == "SpanKind.CLIENT"
        assert client_span["attributes"]["rpc.method"] == method
        assert client_span["attributes"]["rpc.service"] == "helloworld.Greeter"
        assert client_span["attributes"]["rpc.system"] == "grpc"

        assert server_span["context"]["trace_id"] == client_span["context"]["trace_id"]
        assert client_span["context"]["span_id"] == server_span["parent_id"]

        # payloads
        assert server_span["attributes"]["rpc.grpc.request.payload"] == request_payload
        assert client_span["attributes"]["rpc.grpc.request.payload"] == request_payload
        # TODO: collect the response from the server - RD-11068
        # assert server_span["attributes"]["rpc.grpc.response.payload"] == response_payload
        assert (
            client_span["attributes"]["rpc.grpc.response.payload"] == response_payload
        )

        return server_span, client_span

    def test_grpcio_instrumentation_unary_unary(self):
        with GreeterServerApp(), grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHelloUnaryUnary(helloworld_pb2.HelloRequest(name="you"))

            self.assertEqual(response.message, "Hello, you!")
            self.check_spans(
                method="SayHelloUnaryUnary",
                request_payload='name: "you"\n',
                response_payload='message: "Hello, you!"\n',
            )

    def test_grpcio_instrumentation_unary_stream(self):
        with GreeterServerApp(), grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHelloUnaryStream(helloworld_pb2.HelloRequest(name="you"))
            all_responses = list(response)

            self.assertEqual(len(all_responses), 2)
            self.assertEqual(all_responses[0].message, "First hello, you!")
            self.assertEqual(all_responses[1].message, "Second hello, you!")
            self.check_spans(
                method="SayHelloUnaryStream",
                request_payload='name: "you"\n',
                response_payload='message: "First hello, you!"\n,message: "Second hello, you!"\n',
            )

    def test_grpcio_instrumentation_stream_unary(self):
        with GreeterServerApp(), grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHelloStreamUnary(
                iter(
                    (
                        helloworld_pb2.HelloRequest(name="you1"),
                        helloworld_pb2.HelloRequest(name="you2"),
                    )
                )
            )

            self.assertEqual(response.message, "Hello, you1,you2!")
            self.check_spans(
                method="SayHelloStreamUnary",
                request_payload='name: "you1"\n,name: "you2"\n',
                response_payload='message: "Hello, you1,you2!"\n',
            )

    def test_grpcio_instrumentation_stream_stream(self):
        with GreeterServerApp(), grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHelloStreamStream(
                iter(
                    (
                        helloworld_pb2.HelloRequest(name="you1"),
                        helloworld_pb2.HelloRequest(name="you2"),
                    )
                )
            )
            all_responses = list(response)

            self.assertEqual(len(all_responses), 2)
            self.assertEqual(all_responses[0].message, "First hello, you1,you2!")
            self.assertEqual(all_responses[1].message, "Second hello, you1,you2!")
            self.check_spans(
                method="SayHelloStreamStream",
                request_payload='name: "you1"\n,name: "you2"\n',
                response_payload='message: "First hello, you1,you2!"\n,message: "Second hello, you1,you2!"\n',
            )
