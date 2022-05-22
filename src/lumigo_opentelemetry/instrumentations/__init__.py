from typing import List

from lumigo_opentelemetry import logger

from abc import ABC, abstractmethod

# Instrumentations
from .aiohttp_client import instrumentor as aiohttp_client_instrumentor
from .aiopg import instrumentor as aiopg_instrumentor
from .asyncpg import instrumentor as asyncpg_instrumentor
from .botocore import instrumentor as boto_instrumentor
from .django import instrumentor as django_instrumentor
from .elasticsearch import instrumentor as elasticsearch_instrumentor
from .falcon import instrumentor as falcon_instrumentor
from .fastapi import instrumentor as fastapi_instrumentor
from .flask import instrumentor as flask_instrumentor
from .grpc import instrumentor as grpc_instrumentor
from .httpx import instrumentor as httpx_instrumentor
from .jinja2 import instrumentor as jinja2_instrumentor
from .kafka import instrumentor as kafka_instrumentor
from .mysql import instrumentor as mysql_instrumentor
from .pika import instrumentor as pika_instrumentor
from .psycopg2 import instrumentor as psycopg2_instrumentor
from .pymemcache import instrumentor as pymemcache_instrumentor
from .pymongo import instrumentor as pymongo_instrumentor
from .pymysql import instrumentor as pymysql_instrumentor
from .pyramid import instrumentor as pyramid_instrumentor
from .redis import instrumentor as redis_instrumentor
from .requests import instrumentor as requests_instrumentor
from .sklearn import instrumentor as sklearn_instrumentor
from .sqlite3 import instrumentor as sqlite3_instrumentor
from .tornado import instrumentor as tornado_instrumentor
from .urllib import instrumentor as urllib_instrumentor
from .urllib3 import instrumentor as urllib3_instrumentor


class AbstractInstrumentor(ABC):
    """This class wraps around the facilities of opentelemetry.instrumentation.BaseInstrumentor
    to provide a safer baseline in terms of dependency checks than what is available upstream.
    """

    # TODO Implement lookup of package versions based on the file-based version ranges we validate

    @abstractmethod
    def __init__(self, instrumentation_id: str):
        self._instrumentation_id = instrumentation_id

    @abstractmethod
    def check_if_applicable(self):
        raise Exception("'check_if_applicable' method not implemented!")

    @abstractmethod
    def install_instrumentation(self):
        raise Exception("'apply_instrumentation' method not implemented!")

    @property
    def instrumentation_id(self) -> str:
        return self._instrumentation_id


installed_instrumentations: List[str] = []
instrumentors: List[AbstractInstrumentor] = [
    aiohttp_client_instrumentor,
    aiopg_instrumentor,
    asyncpg_instrumentor,
    boto_instrumentor,
    django_instrumentor,
    elasticsearch_instrumentor,
    falcon_instrumentor,
    fastapi_instrumentor,
    flask_instrumentor,
    grpc_instrumentor,
    httpx_instrumentor,
    jinja2_instrumentor,
    kafka_instrumentor,
    mysql_instrumentor,
    pika_instrumentor,
    psycopg2_instrumentor,
    pymemcache_instrumentor,
    pymongo_instrumentor,
    pymysql_instrumentor,
    pyramid_instrumentor,
    redis_instrumentor,
    requests_instrumentor,
    sklearn_instrumentor,
    sqlite3_instrumentor,
    tornado_instrumentor,
    urllib_instrumentor,
    urllib3_instrumentor,
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
        )

logger.debug(
    "Installed instrumentations: %s", ", ".join(list(installed_instrumentations))
)
