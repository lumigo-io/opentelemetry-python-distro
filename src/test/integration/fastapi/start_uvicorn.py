import argparse
import uvicorn


def serve(app, port):
    """Serve the web application."""
    uvicorn.run(app, port=port)


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--app", help="app name")
    argParser.add_argument("--port", type=int, help="port number")
    args = argParser.parse_args()
    serve(args.app, args.port)
