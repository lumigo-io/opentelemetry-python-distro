from typing import List

from lumigo_opentelemetry import logger


# Instrumentations
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

from .boto import instrumentor as boto_instrumentor
from .botocore import instrumentor as botocore_instrumentor
from .fastapi import instrumentor as fastapi_instrumentor
from .flask import instrumentor as flask_instrumentor
from .pymongo import instrumentor as pymongo_instrumentor
from .pymysql import instrumentor as pymysql_instrumentor
from .requests import instrumentor as requests_instrumentor


installed_instrumentations: List[str] = []
instrumentors: List[AbstractInstrumentor] = [
    boto_instrumentor,
    botocore_instrumentor,
    fastapi_instrumentor,
    flask_instrumentor,
    pymongo_instrumentor,
    pymysql_instrumentor,
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
        ],
        installed_instrumentations,
    )
)
framework = frameworks[0] if frameworks else "Unknown"
