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
        "wrapt>=1.11.0",
        "lumigo_core==0.0.16",
        "opentelemetry-api==1.34.1",
        "opentelemetry-sdk==1.34.1",
        "opentelemetry-sdk-extension-aws==2.0.2",
        "opentelemetry-exporter-otlp-proto-http==1.34.1",
        "opentelemetry-semantic-conventions==0.55b1",
        "opentelemetry-instrumentation==0.55b1",
        "opentelemetry-instrumentation-asgi==0.55b1",
        "opentelemetry-instrumentation-aws-lambda==0.55b1",
        "opentelemetry-instrumentation-boto==0.55b1",
        "opentelemetry-instrumentation-fastapi==0.55b1",
        "opentelemetry-instrumentation-flask==0.55b1",
        "opentelemetry-instrumentation-grpc==0.55b1",
        "opentelemetry-instrumentation-kafka-python==0.55b1",
        "opentelemetry-instrumentation-pika==0.55b1",
        "opentelemetry-instrumentation-psycopg2==0.55b1",
        "opentelemetry-instrumentation-pymongo==0.55b1",
        "opentelemetry-instrumentation-pymysql==0.55b1",
        "opentelemetry-instrumentation-requests==0.55b1",
        "opentelemetry-instrumentation-redis==0.55b1",
        "opentelemetry-instrumentation-django==0.55b1",
        "opentelemetry-instrumentation-logging==0.55b1",
        "opentelemetry-instrumentation-langchain==0.46.2",
        "openinference-instrumentation-agno>=0.1.10",
        "typing_extensions==4.7.1; python_version<'3.8'",
        "importlib-metadata==6.7.0; python_version<'3.8'",
        "setuptools<=80.9.0",
    ],
)
