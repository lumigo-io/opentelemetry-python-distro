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
        "opentelemetry-api==1.9.1",
        "opentelemetry-exporter-otlp==1.9.1",
        "opentelemetry-proto==1.9.1",
        "opentelemetry-exporter-zipkin==1.10.0",
        "opentelemetry-exporter-zipkin-json==1.10.0",
        "opentelemetry-exporter-zipkin-proto-http==1.10.0",
        "opentelemetry-sdk==1.9.1",
        "opentelemetry-instrumentation==0.28b1",
        "opentelemetry-instrumentation-boto==0.28b1",
        "opentelemetry-instrumentation-botocore==0.28b1",
        "opentelemetry-instrumentation-flask==0.28b1",
        "opentelemetry-instrumentation-requests==0.28b1",
        "opentelemetry-instrumentation-wsgi==0.28b1",
        "opentelemetry-instrumentation-fastapi==0.28b1",
        "opentelemetry-semantic-conventions==0.28b1",
        "flask==1.1.2",
        "boto3==1.17.22",
        "boto==2.49.0",
        "botocore==1.20.112",
        "fastapi==0.70.1",
        "requests==2.27.1",
        "arnparse==0.0.2",
        "click==8.0.3",
        "importlib-metadata==4.8.2",
        "itsdangerous==2.0.1",
        "Jinja2==3.0.3",
        "MarkupSafe==2.0.1",
        "typing_extensions==4.0.1",
        "Werkzeug==2.0.2",
        "zipp==3.8.0",
    ],
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    long_description=open("README.md").read(),
    package_data={"lumigo-python-wrapper": ["VERSION"]},
)
