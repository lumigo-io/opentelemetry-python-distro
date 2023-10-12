import uvicorn


def serve():
    """Serve the web application."""
    uvicorn.run("app:app", port=8000)


if __name__ == "__main__":
    serve()
