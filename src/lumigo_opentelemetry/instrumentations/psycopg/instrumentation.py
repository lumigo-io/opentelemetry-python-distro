# mypy: ignore-errors

# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# MODIFICATIONS from opentelemetry-python-contrib psycopg2 instrumentation:
# https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/opentelemetry-instrumentation-psycopg2/src/opentelemetry/instrumentation/psycopg2/__init__.py
# pg_cursor (cursor imported from psycopg.extensions) -> psycopg.Cursor

"""
The integration with PostgreSQL supports the `Psycopg`_ library (Psycopg3), it can be enabled by
using ``PsycopgInstrumentor``.

.. _Psycopg: https://www.psycopg.org/psycopg3/

SQLCOMMENTER
*****************************************
You can optionally configure Psycopg instrumentation to enable sqlcommenter which enriches
the query with contextual information.

Usage
-----

.. code:: python

    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

    PsycopgInstrumentor().instrument(enable_commenter=True, commenter_options={})


For example,
::

   Invoking cursor.execute("select * from auth_users") will lead to sql query "select * from auth_users" but when SQLCommenter is enabled
   the query will get appended with some configurable tags like "select * from auth_users /*tag=value*/;"


SQLCommenter Configurations
***************************
We can configure the tags to be appended to the sqlquery log by adding configuration inside commenter_options(default:{}) keyword

db_driver = True(Default) or False

For example,
::
Enabling this flag will add psycopg and it's version which is /*psycopg%%3A3.0*/

dbapi_threadsafety = True(Default) or False

For example,
::
Enabling this flag will add threadsafety /*dbapi_threadsafety=2*/

dbapi_level = True(Default) or False

For example,
::
Enabling this flag will add dbapi_level /*dbapi_level='2.0'*/

libpq_version = True(Default) or False

For example,
::
Enabling this flag will add libpq_version /*libpq_version=140001*/

driver_paramstyle = True(Default) or False

For example,
::
Enabling this flag will add driver_paramstyle /*driver_paramstyle='pyformat'*/

opentelemetry_values = True(Default) or False

For example,
::
Enabling this flag will add traceparent values /*traceparent='00-03afa25236b8cd948fa853d67038ac79-405ff022e8247c46-01'*/

Usage
-----

.. code-block:: python

    import psycopg
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor


    PsycopgInstrumentor().instrument()

    cnx = psycopg.connect(database='Database')
    cursor = cnx.cursor()
    cursor.execute("INSERT INTO test (testField) VALUES (123)")
    cursor.close()
    cnx.close()

API
---
"""

import logging
import typing
from typing import Collection

import psycopg
from opentelemetry.instrumentation import dbapi
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from psycopg.sql import Composed  # pylint: disable=no-name-in-module

from .package import _instruments
from .version import __version__

_logger = logging.getLogger(__name__)
_OTEL_CURSOR_FACTORY_KEY = "_otel_orig_cursor_factory"


class PsycopgInstrumentor(BaseInstrumentor):
    _CONNECTION_ATTRIBUTES = {
        "database": "info.dbname",
        "port": "info.port",
        "host": "info.host",
        "user": "info.user",
    }

    _DATABASE_SYSTEM = "postgresql"

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        """Integrate with PostgreSQL Psycopg library.
        Psycopg: https://www.psycopg.org/psycopg3/
        """
        tracer_provider = kwargs.get("tracer_provider")
        enable_sqlcommenter = kwargs.get("enable_commenter", False)
        commenter_options = kwargs.get("commenter_options", {})
        dbapi.wrap_connect(
            __name__,
            psycopg,
            "connect",
            self._DATABASE_SYSTEM,
            self._CONNECTION_ATTRIBUTES,
            version=__version__,
            tracer_provider=tracer_provider,
            db_api_integration_factory=DatabaseApiIntegration,
            enable_commenter=enable_sqlcommenter,
            commenter_options=commenter_options,
        )

    def _uninstrument(self, **kwargs):
        """ "Disable Psycopg2 instrumentation"""
        dbapi.unwrap_connect(psycopg, "connect")

    # TODO(owais): check if core dbapi can do this for all dbapi implementations e.g, pymysql and mysql
    @staticmethod
    def instrument_connection(connection, tracer_provider=None):
        if not hasattr(connection, "_is_instrumented_by_opentelemetry"):
            connection._is_instrumented_by_opentelemetry = False

        if not connection._is_instrumented_by_opentelemetry:
            setattr(connection, _OTEL_CURSOR_FACTORY_KEY, connection.cursor_factory)
            connection.cursor_factory = _new_cursor_factory(
                tracer_provider=tracer_provider
            )
            connection._is_instrumented_by_opentelemetry = True
        else:
            _logger.warning(
                "Attempting to instrument Psycopg connection while already instrumented"
            )
        return connection

    # TODO(owais): check if core dbapi can do this for all dbapi implementations e.g, pymysql and mysql
    @staticmethod
    def uninstrument_connection(connection):
        connection.cursor_factory = getattr(connection, _OTEL_CURSOR_FACTORY_KEY, None)

        return connection


# TODO(owais): check if core dbapi can do this for all dbapi implementations e.g, pymysql and mysql
class DatabaseApiIntegration(dbapi.DatabaseApiIntegration):
    def wrapped_connection(
        self,
        connect_method: typing.Callable[..., typing.Any],
        args: typing.Tuple[typing.Any, typing.Any],
        kwargs: typing.Dict[typing.Any, typing.Any],
    ):
        """Add object proxy to connection object."""
        base_cursor_factory = kwargs.pop("cursor_factory", None)
        new_factory_kwargs = {"db_api": self}
        if base_cursor_factory:
            new_factory_kwargs["base_factory"] = base_cursor_factory
        kwargs["cursor_factory"] = _new_cursor_factory(**new_factory_kwargs)
        connection = connect_method(*args, **kwargs)
        self.get_connection_attributes(connection)
        return connection


class CursorTracer(dbapi.CursorTracer):
    def get_operation_name(self, cursor, args):
        if not args:
            return ""

        statement = args[0]
        if isinstance(statement, Composed):
            statement = statement.as_string(cursor)

        if isinstance(statement, str):
            # Strip leading comments so we get the operation name.
            return self._leading_comment_remover.sub("", statement).split()[0]

        return ""

    def get_statement(self, cursor, args):
        if not args:
            return ""

        statement = args[0]
        if isinstance(statement, Composed):
            statement = statement.as_string(cursor)
        return statement


def _new_cursor_factory(db_api=None, base_factory=None, tracer_provider=None):
    if not db_api:
        db_api = DatabaseApiIntegration(
            __name__,
            PsycopgInstrumentor._DATABASE_SYSTEM,
            connection_attributes=PsycopgInstrumentor._CONNECTION_ATTRIBUTES,
            version=__version__,
            tracer_provider=tracer_provider,
        )

    base_factory = base_factory or psycopg.Cursor
    _cursor_tracer = CursorTracer(db_api)

    class TracedCursorFactory(base_factory):
        def execute(self, *args, **kwargs):
            return _cursor_tracer.traced_execution(
                self, super().execute, *args, **kwargs
            )

        def executemany(self, *args, **kwargs):
            return _cursor_tracer.traced_execution(
                self, super().executemany, *args, **kwargs
            )

        def callproc(self, *args, **kwargs):
            return _cursor_tracer.traced_execution(
                self, super().callproc, *args, **kwargs
            )

    return TracedCursorFactory
