# Copyright 2015 gRPC authors.
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
"""The Python implementation of the GRPC helloworld.Greeter server."""

import os
import sys
from concurrent import futures

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/protos")

import grpc  # noqa: E402
import helloworld_pb2  # noqa: E402
import helloworld_pb2_grpc  # noqa: E402


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)


class ClientTestServer:
    def __init__(self, port: str = "50052"):
        self.port = port
        self.running = False
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), self.server)
        self.server.add_insecure_port("[::]:" + self.port)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def start(self):
        if self.running:
            print("Greeter client test server already started")
            return
        self.server.start()
        self.running = True
        print("Greeter client test server started, listening on " + self.port)

    def stop(self):
        if self.running:
            self.server.stop(0)
        else:
            print("Greeter client test server not running")
