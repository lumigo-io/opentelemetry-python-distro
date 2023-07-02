import time
import unittest
from test.test_utils.spans_parser import SpansContainer

from .client_test_server import ClientTestServer


class TestGrpcSpans(unittest.TestCase):
    def test_grpc_greeting_client(self):
        with ClientTestServer("50052"):
            time.sleep(1)  # wait for client to attempt connection
            time.sleep(3)  # wait for spans to be posted
