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
        "opentelemetry-api==1.9.1",
        "opentelemetry-sdk==1.9.1",
        "opentelemetry-sdk-extension-aws==2.0.1",
        "opentelemetry-exporter-otlp-proto-http==1.9.1",
        "opentelemetry-semantic-conventions==0.28b1",
        "opentelemetry-instrumentation==0.28b1",
        "opentelemetry-instrumentation-aiohttp-client==0.28b1",
        "opentelemetry-instrumentation-aiopg==0.28b1",
        "opentelemetry-instrumentation-asgi==0.28b1",
        "opentelemetry-instrumentation-asyncpg==0.28b1",
        "opentelemetry-instrumentation-boto==0.28b1",
        "opentelemetry-instrumentation-boto3sqs==0.33b0",
        "opentelemetry-instrumentation-botocore==0.28b1",
        "opentelemetry-instrumentation-django==0.28b1",
        "opentelemetry-instrumentation-elasticsearch==0.28b1",
        "opentelemetry-instrumentation-falcon==0.28b1",
        "opentelemetry-instrumentation-fastapi==0.28b1",
        "opentelemetry-instrumentation-flask==0.28b1",
        "opentelemetry-instrumentation-grpc==0.28b1",
        "opentelemetry-instrumentation-httpx==0.28b1",
        "opentelemetry-instrumentation-jinja2==0.28b1",
        "opentelemetry-instrumentation-kafka-python==0.28b1",
        "opentelemetry-instrumentation-logging==0.28b1",
        "opentelemetry-instrumentation-mysql==0.28b1",
        "opentelemetry-instrumentation-pika==0.28b1",
        "opentelemetry-instrumentation-psycopg2==0.28b1",
        "opentelemetry-instrumentation-pymemcache==0.28b1",
        "opentelemetry-instrumentation-pymongo==0.28b1",
        "opentelemetry-instrumentation-pymysql==0.28b1",
        "opentelemetry-instrumentation-pyramid==0.28b1",
        "opentelemetry-instrumentation-redis==0.28b1",
        "opentelemetry-instrumentation-requests==0.28b1",
        "opentelemetry-instrumentation-sklearn==0.28b1",
        "opentelemetry-instrumentation-sqlite3==0.28b1",
        "opentelemetry-instrumentation-tornado==0.28b1",
        "opentelemetry-instrumentation-urllib==0.28b1",
        "opentelemetry-instrumentation-urllib3==0.28b1",
        "opentelemetry-instrumentation-wsgi==0.28b1",
    ],
)
