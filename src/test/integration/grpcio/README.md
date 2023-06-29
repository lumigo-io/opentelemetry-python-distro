# gRPC tests

The `greeter_server.py` and `helloworld.proto` files are lifted directly from the [gRPC examples](https://github.com/grpc/grpc/tree/master/examples).

Follow the [basics tutorial](https://grpc.io/docs/languages/python/basics/) or the [quick start guide](https://grpc.io/docs/languages/python/quickstart/) if you're unfamiliar with gRPC.

To compile the protocol buffers defined in the `protos` folder, either run the test with `nox` (see the main [README](../../../../README.md) file), or activate a virtual environment in the `src/test/integration/grpcio` folder and then run:

```bash
scripts/rebuild_protos
```

This will compile any `.proto` files in the `protos` directory.
