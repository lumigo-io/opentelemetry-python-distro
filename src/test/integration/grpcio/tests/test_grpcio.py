import time
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from test.test_utils.spans_parser import SpansContainer  # noqa: E402

import grpc  # noqa: E402
import helloworld_pb2  # noqa: E402
import helloworld_pb2_grpc  # noqa: E402


class TestGrpcioSpans(unittest.TestCase):
    def test_grpcio_instrumentation(self):
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
        print("Greeter client received: " + response.message)

        self.assertEqual(response.message, "Hello, you!")

        # TODO Do something deterministic
        time.sleep(5)  # allow the exporter to catch up

        server_file = os.getenv("SERVER_SPANDUMP")
        server_spans = SpansContainer.get_spans_from_file(server_file)
        client_spans = SpansContainer.get_spans_from_file()

        assert len(server_spans.spans) == 1
        server_span = server_spans.spans[0]
        assert server_span["kind"] == "SpanKind.SERVER"
        assert server_span["attributes"]["rpc.method"] == "SayHello"
        assert server_span["attributes"]["rpc.service"] == "helloworld.Greeter"
        assert server_span["attributes"]["rpc.system"] == "grpc"
        assert server_span["attributes"]["rpc.payload"] == 'name: "you"\n'

        assert len(client_spans.spans) == 1
        client_span = client_spans.spans[0]
        assert client_span["kind"] == "SpanKind.CLIENT"
        assert client_span["attributes"]["rpc.method"] == "SayHello"
        assert client_span["attributes"]["rpc.service"] == "helloworld.Greeter"
        assert client_span["attributes"]["rpc.system"] == "grpc"
        assert client_span["attributes"]["rpc.payload"] == 'name: "you"\n'

        assert server_span["context"]["trace_id"] == client_span["context"]["trace_id"]
        assert client_span["context"]["span_id"] == server_span["parent_id"]
