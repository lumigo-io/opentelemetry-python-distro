import os

import setuptools


VERSION_PATH = os.path.join(
    os.path.dirname(__file__), "src", "lumigo_wrapper", "VERSION"
)

setuptools.setup(
    name="lumigo-python-wrapper",
    version=open(VERSION_PATH).read(),
    author="Lumigo LTD (https://lumigo.io)",
    author_email="support@lumigo.io",
    description="Lumigo wrapper to trace distributed architecture",
    url="https://github.com/lumigo-io/lumigo-python-wrapper.git",
    package_dir={"": "src"},
    packages=setuptools.find_packages("src", exclude=["test"]),
    install_requires=[
        "asgiref==3.5.2",
        "packaging==21.3",
        "wrapt==1.14.1",
        "opentelemetry-sdk==1.9.1",
        "opentelemetry-api==1.9.1",
        "opentelemetry-exporter-zipkin==1.10.0",
        "opentelemetry-exporter-zipkin-json==1.10.0",
        "opentelemetry-exporter-zipkin-proto-http==1.10.0",
        "opentelemetry-semantic-conventions==0.28b1",
        "opentelemetry-instrumentation==0.28b1",
        "opentelemetry-instrumentation-aiohttp-client==0.28b1",
        "opentelemetry-instrumentation-aiopg==0.28b1",
        "opentelemetry-instrumentation-asgi==0.28b1",
        "opentelemetry-instrumentation-asyncpg==0.28b1",
        "opentelemetry-instrumentation-boto==0.28b1",
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
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    long_description=open("README.md").read(),
    package_data={"lumigo-python-wrapper": ["VERSION"]},
)
