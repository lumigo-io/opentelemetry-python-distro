import argparse

from flask_app import app

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--port", type=int, help="port number")
    args = argParser.parse_args()
    app.run(host="0.0.0.0", port=args.port)
