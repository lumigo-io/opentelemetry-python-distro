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
        "opentelemetry-api==1.39.1",
        "opentelemetry-sdk==1.39.1",
        "opentelemetry-sdk-extension-aws==2.1.0",
        "opentelemetry-exporter-otlp-proto-http @ git+https://github.com/moshe-shaham-lumigo/opentelemetry-python.git@remove-requests-package#subdirectory=exporter/opentelemetry-exporter-otlp-proto-http",
        "opentelemetry-semantic-conventions==0.60b1",
        "opentelemetry-instrumentation==0.60b1",
        "opentelemetry-instrumentation-asgi==0.60b1",
        "opentelemetry-instrumentation-aws-lambda==0.60b1",
        "opentelemetry-instrumentation-boto==0.60b1",
        "opentelemetry-instrumentation-fastapi==0.60b1",
        "opentelemetry-instrumentation-flask==0.60b1",
        "opentelemetry-instrumentation-grpc==0.60b1",
        "opentelemetry-instrumentation-kafka-python==0.60b1",
        "opentelemetry-instrumentation-pika==0.60b1",
        "opentelemetry-instrumentation-psycopg2==0.60b1",
        "opentelemetry-instrumentation-pymongo==0.60b1",
        "opentelemetry-instrumentation-pymysql==0.60b1",
        "opentelemetry-instrumentation-requests==0.60b1",
        "opentelemetry-instrumentation-redis==0.60b1",
        "opentelemetry-instrumentation-django==0.60b1",
        "opentelemetry-instrumentation-logging==0.60b1",
        "opentelemetry-instrumentation-httpx==0.60b1",
        "opentelemetry-instrumentation-langchain==0.50.1",
        "openinference-instrumentation-agno==0.1.25",
        "typing_extensions==4.7.1; python_version<'3.8'",
        "importlib-metadata==6.7.0; python_version<'3.8'",
        "setuptools<=80.9.0",
    ],
)
