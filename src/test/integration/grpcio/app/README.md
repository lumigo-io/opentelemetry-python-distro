This app is mainly based on the GRPC client/server example:
https://grpc.io/docs/languages/python/quickstart/

The file `helloworld.proto` has changed to measure all the `unary X stream` options of the requestand response.
To recompile this proto file and regenerate the files `helloworld_pb2.py, helloworld_pb2.pyi, helloworld_pb2_grpc.py` use:
```
python -m grpc_tools.protoc helloworld.proto -I. --python_out=. --pyi_out=. --grpc_python_out=.
```
