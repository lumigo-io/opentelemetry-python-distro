import os
import sys
import time
import unittest
from test.test_utils.spans_parser import SpansContainer

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/protos")

import grpc  # noqa: E402
import helloworld_pb2  # noqa: E402
import helloworld_pb2_grpc  # noqa: E402


class TestGrpcSpans(unittest.TestCase):
    def test_grpc_greeting_server(self):
        test_server = "localhost:50051"
        with grpc.insecure_channel(test_server) as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
        print("Greeter client received: " + response.message)
        assert response.message == "Hello, you!"

        time.sleep(3)  # wait for spans to be posted

        with grpc.insecure_channel(test_server) as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="me"))
        print("Greeter client received: " + response.message)
        assert response.message == "Hello, me!"
