from typing import List

from lumigo_opentelemetry import logger

# Instrumentations
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

from .boto import instrumentor as boto_instrumentor
from .botocore import instrumentor as botocore_instrumentor
from .django import instrumentor as django_instrumentor
from .fastapi import instrumentor as fastapi_instrumentor
from .flask import instrumentor as flask_instrumentor
from .grpcio import instrumentor as grpc_instrumentor
from .kafka_python import instrumentor as kafka_python_instrumentor
from .pika import instrumentor as pika_instrumentor
from .psycopg import instrumentor as psycopg_instrumentor
from .psycopg2 import instrumentor as psycopg2_instrumentor
from .pymongo import instrumentor as pymongo_instrumentor
from .pymysql import instrumentor as pymysql_instrumentor
from .redis import instrumentor as redis_instrumentor
from .requests import instrumentor as requests_instrumentor

installed_instrumentations: List[str] = []
instrumentors: List[AbstractInstrumentor] = [
    boto_instrumentor,
    botocore_instrumentor,
    django_instrumentor,
    fastapi_instrumentor,
    flask_instrumentor,
    grpc_instrumentor,
    kafka_python_instrumentor,
    pika_instrumentor,
    psycopg_instrumentor,
    psycopg2_instrumentor,
    pymongo_instrumentor,
    pymysql_instrumentor,
    redis_instrumentor,
    requests_instrumentor,
]
for instrumentor in instrumentors:
    try:
        instrumentor.check_if_applicable()
    except ImportError:
        continue

    try:
        instrumentor.install_instrumentation()
        installed_instrumentations.append(instrumentor.instrumentation_id)
    except Exception as e:
        # TODO Send to backend as event to look into
        logger.error(
            "An error occurred while applying the '%s' instrumentation: %s",
            instrumentor.instrumentation_id,
            str(e),
            exc_info=True,
        )

logger.debug(
    "Installed instrumentations: %s", ", ".join(list(installed_instrumentations))
)

frameworks = list(
    filter(
        lambda instrumentor_id: instrumentor_id
        in [
            fastapi_instrumentor.instrumentation_id,
            flask_instrumentor.instrumentation_id,
            django_instrumentor.instrumentation_id,
        ],
        installed_instrumentations,
    )
)
framework = frameworks[0] if frameworks else "Unknown"
