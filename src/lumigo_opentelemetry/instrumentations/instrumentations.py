from os import environ
from typing import List

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.instrumentations import (
    AbstractInstrumentor,
    MissingDependencyException,
    UnsupportedDependencyVersionException,
    SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME,
)

DISABLED_INSTRUMENTATIONS_ENV_VAR_NAME = "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"

from .boto import BotoInstrumentor
from .botocore import BotoCoreInstrumentor
from .fastapi import FastApiInstrumentor
from .flask import FlaskInstrumentor
from .pymongo import PymongoInstrumentor
from .pymysql import PyMySqlInstrumentor
from .requests import RequestsInstrumentor

fastapi_instrumentor = FastApiInstrumentor()
flask_instrumentor = FlaskInstrumentor()

instrumentors: List[AbstractInstrumentor] = [
    fastapi_instrumentor,
    flask_instrumentor,
    BotoInstrumentor(),
    BotoCoreInstrumentor(),
    PymongoInstrumentor(),
    PyMySqlInstrumentor(),
    RequestsInstrumentor(),
]

disabled_instrumentations = [
    instrumentation.strip()
    for instrumentation in environ.get(
        DISABLED_INSTRUMENTATIONS_ENV_VAR_NAME, ""
    ).split(",")
]

logger.debug(
    f"Disabled instrumentations: {', '.join(disabled_instrumentations) or 'none'}"
)

instrumentors_to_attempt = [
    instrumentor
    for instrumentor in instrumentors
    if instrumentor.instrumentation_id not in disabled_instrumentations
]

installed_instrumentations: List[str] = []
for instrumentor in instrumentors_to_attempt:
    try:
        instrumentor.install_instrumentation()
        installed_instrumentations.append(instrumentor.instrumentation_id)
    except MissingDependencyException as e:
        logger.debug(
            "Skipping the '%s' instrumentation due to the missing '%s' dependency",
            instrumentor.instrumentation_id,
            e.package_name,
        )
    except UnsupportedDependencyVersionException as e:
        current_disabled_instrumentations_value = environ.get(
            DISABLED_INSTRUMENTATIONS_ENV_VAR_NAME, ""
        )
        current_skip_checks_value = environ.get(
            SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME, ""
        )

        instr = instrumentor.instrumentation_id
        message = (
            "Incompatible version '{v}' of the '{p}' package found for the '{i}' instrumentation: "
            "the '{p}' package will not be not instrumented; to suppress this log, set the '{dn}={dv}' "
            "environment variable; instead, to suppress this compatibility check, set the '{en}={ev}' environment variable".format(
                v=e.version_found,
                p=e.package_name,
                i=instr,
                dn=DISABLED_INSTRUMENTATIONS_ENV_VAR_NAME,
                dv=(
                    current_disabled_instrumentations_value + "," + instr
                    if current_disabled_instrumentations_value
                    else instr
                ),
                en=SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME,
                ev=(
                    current_skip_checks_value + "," + instr
                    if current_skip_checks_value
                    else instr
                ),
            )
        )
        logger.warn(message)
    except Exception:
        # TODO Send to backend as event to look into
        logger.exception(
            "An error occurred while applying the '%s' instrumentation",
            instrumentor.instrumentation_id,
        )

logger.debug(
    "Installed instrumentations: %s",
    ", ".join(list(installed_instrumentations))
    if installed_instrumentations
    else "none",
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
