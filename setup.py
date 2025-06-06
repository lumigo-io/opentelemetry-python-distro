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
        "lumigo_core==0.0.10",
        "opentelemetry-api==1.26.0",
        "opentelemetry-sdk==1.26.0",
        "opentelemetry-sdk-extension-aws==2.0.2",
        "opentelemetry-exporter-otlp-proto-http==1.26.0",
        "opentelemetry-semantic-conventions==0.47b0",
        "opentelemetry-instrumentation==0.47b0",
        "opentelemetry-instrumentation-asgi==0.47b0",
        "opentelemetry-instrumentation-boto==0.47b0",
        "opentelemetry-instrumentation-fastapi==0.47b0",
        "opentelemetry-instrumentation-flask==0.47b0",
        "opentelemetry-instrumentation-grpc==0.47b0",
        "opentelemetry-instrumentation-kafka-python==0.47b0",
        "opentelemetry-instrumentation-pika==0.47b0",
        "opentelemetry-instrumentation-psycopg2==0.47b0",
        "opentelemetry-instrumentation-pymongo==0.47b0",
        "opentelemetry-instrumentation-pymysql==0.47b0",
        "opentelemetry-instrumentation-requests==0.47b0",
        "opentelemetry-instrumentation-redis==0.47b0",
        "opentelemetry-instrumentation-django==0.47b0",
        "opentelemetry-instrumentation-logging==0.47b0",
        # v4.7.1 is the last version that supports python 3.7
        "typing_extensions==4.12.2; python_version<'3.8'",
        # v6.7.0 is the last version that supports python 3.7
        "importlib-metadata==6.7.0; python_version<'3.8'",
    ],
)
