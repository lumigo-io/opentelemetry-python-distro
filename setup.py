import os

from setuptools import setup

VERSION_PATH = os.path.join(
    os.path.dirname(__file__), "src", "lumigo_opentelemetry", "VERSION"
)

setup(
    version=open(VERSION_PATH).read(),
    package_data={"lumigo_opentelemetry": ["VERSION"]},
    entry_points={
        "lumigo_opentelemetry": ["string = lumigo_opentelemetry:auto_load"],
    },
    install_requires=[
        "asgiref~=3.0",
        "autowrapt>=1.0",
        "protobuf>=3.13.0, <4.0.0",
        "wrapt>=1.11.0",
        "lumigo_tracer==1.1.213",
        "opentelemetry-api==1.15.0",
        "opentelemetry-sdk==1.15.0",
        "opentelemetry-sdk-extension-aws==2.0.1",
        "opentelemetry-exporter-otlp-proto-http==1.15.0",
        "opentelemetry-semantic-conventions==0.36b0",
        "opentelemetry-instrumentation==0.36b0",
        "opentelemetry-instrumentation-asgi==0.36b0",
        "opentelemetry-instrumentation-boto==0.36b0",
        "opentelemetry-instrumentation-fastapi==0.36b0",
        "opentelemetry-instrumentation-flask==0.36b0",
        "opentelemetry-instrumentation-pymongo==0.36b0",
        "opentelemetry-instrumentation-pymysql==0.36b0",
        "opentelemetry-instrumentation-requests==0.36b0",
    ],
)
