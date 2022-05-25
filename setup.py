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
        "asgiref==3.5.2",
        "autowrapt>=1.0",
        "packaging>=21.3",
        "wrapt>=1.11.0",
        "opentelemetry-api==1.11.1",
        "opentelemetry-sdk==1.11.1",
        "opentelemetry-exporter-otlp-proto-http==1.11.1",
        "opentelemetry-semantic-conventions==0.30b1",
        "opentelemetry-instrumentation==0.30b1",
        "opentelemetry-instrumentation-aiohttp-client==0.30b1",
        "opentelemetry-instrumentation-aiopg==0.30b1",
        "opentelemetry-instrumentation-asgi==0.30b1",
        "opentelemetry-instrumentation-asyncpg==0.30b1",
        "opentelemetry-instrumentation-boto==0.30b1",
        "opentelemetry-instrumentation-botocore==0.30b1",
        "opentelemetry-instrumentation-django==0.30b1",
        "opentelemetry-instrumentation-elasticsearch==0.30b1",
        "opentelemetry-instrumentation-falcon==0.30b1",
        "opentelemetry-instrumentation-fastapi==0.30b1",
        "opentelemetry-instrumentation-flask==0.30b1",
        "opentelemetry-instrumentation-grpc==0.30b1",
        "opentelemetry-instrumentation-httpx==0.30b1",
        "opentelemetry-instrumentation-jinja2==0.30b1",
        "opentelemetry-instrumentation-kafka-python==0.30b1",
        "opentelemetry-instrumentation-logging==0.30b1",
        "opentelemetry-instrumentation-mysql==0.30b1",
        "opentelemetry-instrumentation-pika==0.30b1",
        "opentelemetry-instrumentation-psycopg2==0.30b1",
        "opentelemetry-instrumentation-pymemcache==0.30b1",
        "opentelemetry-instrumentation-pymongo==0.30b1",
        "opentelemetry-instrumentation-pymysql==0.30b1",
        "opentelemetry-instrumentation-pyramid==0.30b1",
        "opentelemetry-instrumentation-redis==0.30b1",
        "opentelemetry-instrumentation-requests==0.30b1",
        "opentelemetry-instrumentation-sklearn==0.30b1",
        "opentelemetry-instrumentation-sqlite3==0.30b1",
        "opentelemetry-instrumentation-tornado==0.30b1",
        "opentelemetry-instrumentation-urllib==0.30b1",
        "opentelemetry-instrumentation-urllib3==0.30b1",
        "opentelemetry-instrumentation-wsgi==0.30b1",
    ],
)
