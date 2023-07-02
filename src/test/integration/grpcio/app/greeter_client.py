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

import logging
import os
import sys
import time

parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/protos")

import grpc  # noqa: E402
import helloworld_pb2  # noqa: E402
import helloworld_pb2_grpc  # noqa: E402


def attempt_connection():
    counter = 0
    while counter < 10:
        counter += 1
        try:
            with grpc.insecure_channel("localhost:50052") as channel:
                stub = helloworld_pb2_grpc.GreeterStub(channel)
                response = stub.SayHello(helloworld_pb2.HelloRequest(name="you"))
            print("Greeter client received: " + response.message)
            assert response.message == "Hello, you!"
            print(f"Greeter client attempt {counter} succeeded")
            return
        except Exception as e:
            print(f"Greeter client attempt {counter} threw an exception: {e}")
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig()
    attempt_connection()
