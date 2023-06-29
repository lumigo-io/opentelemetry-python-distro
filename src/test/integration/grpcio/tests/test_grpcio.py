import os
import sys

print("this is what you're looking for!", file=sys.stderr)
print(sys.path, file=sys.stderr)
# get current working dir
print(os.getcwd(), file=sys.stderr)
import os
import sys
import unittest
from test.test_utils.spans_parser import SpansContainer

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/protos")

import grpc
import helloworld_pb2
import helloworld_pb2_grpc


class TestGrpcSpans(unittest.TestCase):
    def test_grpc_greeting(self):
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
        print("Greeter client received: " + response.message)
        assert response.message == "Hello, you!"
