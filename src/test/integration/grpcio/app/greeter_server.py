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
import threading
from concurrent import futures
from typing import Iterable

import grpc
import helloworld_pb2
import helloworld_pb2_grpc

done = threading.Event()


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHelloUnaryUnary(self, request, context):
        return helloworld_pb2.HelloReply(message="Hello, %s!" % request.name)

    def SayHelloUnaryStream(
        self, request, context
    ) -> Iterable[helloworld_pb2.HelloReply]:
        yield helloworld_pb2.HelloReply(message="First hello, %s!" % request.name)
        yield helloworld_pb2.HelloReply(message="Second hello, %s!" % request.name)

    def SayHelloStreamUnary(self, request_iterator, context):
        return helloworld_pb2.HelloReply(
            message="Hello, %s!" % ",".join([r.name for r in request_iterator])
        )

    def SayHelloStreamStream(self, request_iterator, context):
        name = ",".join([r.name for r in request_iterator])
        yield helloworld_pb2.HelloReply(message="First hello, %s!" % name)
        yield helloworld_pb2.HelloReply(message="Second hello, %s!" % name)


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"Server started, listening on port {port}", flush=True)
    # wait until the server process is killed
    done.wait()
    server.stop(1).wait()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
