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
        "opentelemetry-api==1.12",
        "opentelemetry-sdk==1.12",
        "opentelemetry-sdk-extension-aws==2.0.1",
        "opentelemetry-exporter-otlp-proto-http==1.9.1",
        "opentelemetry-semantic-conventions==0.33b0",
        "opentelemetry-instrumentation==0.33b0",
        "opentelemetry-instrumentation-aiohttp-client==0.33b0",
        "opentelemetry-instrumentation-aiopg==0.33b0",
        "opentelemetry-instrumentation-asgi==0.33b0",
        "opentelemetry-instrumentation-asyncpg==0.33b0",
        "opentelemetry-instrumentation-boto==0.33b0",
        "opentelemetry-instrumentation-botocore @ git+https://github.com/lumigo-io/opentelemetry-python-contrib@botocore-sqs-messaging-system#egg=opentelemetry-instrumentation-botocore&subdirectory=instrumentation/opentelemetry-instrumentation-botocore",
        "opentelemetry-instrumentation-django==0.33b0",
        "opentelemetry-instrumentation-elasticsearch==0.33b0",
        "opentelemetry-instrumentation-falcon==0.33b0",
        "opentelemetry-instrumentation-fastapi==0.33b0",
        "opentelemetry-instrumentation-flask==0.33b0",
        "opentelemetry-instrumentation-grpc==0.33b0",
        "opentelemetry-instrumentation-httpx==0.33b0",
        "opentelemetry-instrumentation-jinja2==0.33b0",
        "opentelemetry-instrumentation-kafka-python==0.33b0",
        "opentelemetry-instrumentation-logging==0.33b0",
        "opentelemetry-instrumentation-mysql==0.33b0",
        "opentelemetry-instrumentation-pika==0.33b0",
        "opentelemetry-instrumentation-psycopg2==0.33b0",
        "opentelemetry-instrumentation-pymemcache==0.33b0",
        "opentelemetry-instrumentation-pymongo==0.33b0",
        "opentelemetry-instrumentation-pymysql==0.33b0",
        "opentelemetry-instrumentation-pyramid==0.33b0",
        "opentelemetry-instrumentation-redis==0.33b0",
        "opentelemetry-instrumentation-requests==0.33b0",
        "opentelemetry-instrumentation-sklearn==0.33b0",
        "opentelemetry-instrumentation-sqlite3==0.33b0",
        "opentelemetry-instrumentation-tornado==0.33b0",
        "opentelemetry-instrumentation-urllib==0.33b0",
        "opentelemetry-instrumentation-urllib3==0.33b0",
        "opentelemetry-instrumentation-wsgi==0.33b0",
    ],
)
