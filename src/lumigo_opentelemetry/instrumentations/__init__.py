from abc import abstractmethod, ABC
from os import getenv, listdir, path
from importlib import resources
from pkg_resources import get_distribution, resource_stream, DistInfoDistribution
from re import compile, search
from typing import List, Optional
from wrapt import patch_function_wrapper

from lumigo_opentelemetry import logger
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

_SPLIT_VERSION_FROM_COMMENT_PATTERN = compile(
    r"(?:\s*)(?:!)?(?:\s*)([^\s]+)(?:\s*#\s*(.*))?"
)

SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME = "LUMIGO_SKIP_COMPATIBILITY_CHECKS"


class AbstractInstrumentor(ABC):
    """This class wraps around the facilities of opentelemetry.instrumentation.BaseInstrumentor
    to provide a safer baseline in terms of dependency checks than what is available upstream.
    """

    @abstractmethod
    def __init__(self, instrumentation_id: str):
        self._instrumentation_id = instrumentation_id

    @property
    def instrumentation_id(self) -> str:
        return self._instrumentation_id

    @abstractmethod
    def get_otel_instrumentor(self) -> BaseInstrumentor:
        """Generator method for OpenTelemetry instrumentors.

        Implementations of BaseInstrumentor have the very bad
        habit of hard-requiring with 'import' clauses the
        packages they instrument. Usually, in the __init__.
        That is, by importing the type of OpenTelemetry
        instrumentor to instantiate, we may cause the attempt
        to load code that does not exist in the instrumented
        application and trigger ModuleNotFoundError or the like.
        Therefore, implementations of this method should have
        the import clause inside, rather than at package level,
        to avoid issues with imports in __init__.
        """
        raise Exception("'get_otel_instrumentor' method not implemented!")

    def install_instrumentation(self):
        # We have now the OpenTelemetry instrumentor. If our instrumentation has
        # specialized 'tested_versions' data, let's compare it with what is in
        # the application.
        compatibility_checks_to_skip = [
            instrumentation_id.strip()
            for instrumentation_id in getenv(
                SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME, ""
            ).split(",")
        ]

        tested_versions_resource_dir = path.join(
            resources.files("lumigo_opentelemetry"),
            "instrumentations",
            self.instrumentation_id,
            "tested_versions",
        )

        compatibility_already_checked = False
        if self.instrumentation_id in compatibility_checks_to_skip:
            logger.debug(
                "Skipping compatibility check for the '%s' instrumentation: it is listed in the value of the '%s' environment variable",
                self.instrumentation_id,
                SKIP_COMPATIBILITY_CHECKS_ENV_VAR_NAME,
            )
            # Skip also built-in checks of the upstream OpenTelemetry instrumentor
            compatibility_already_checked = True
        elif not path.isdir(tested_versions_resource_dir):
            logger.debug(
                "No tested_versions data found for the '%s' instrumentation at",
                self.instrumentation_id,
            )
            # No tested_versions found, will rely on the built-in OpenTelemetry instrumentor checks
        else:
            # Check the actual compatibility
            for tested_versions_file in listdir(tested_versions_resource_dir):
                package_name = str(tested_versions_file)

                distribution: DistInfoDistribution = None
                try:
                    distribution = get_distribution(package_name)
                except Exception as e:
                    raise MissingDependencyException(package_name) from e

                with resource_stream(
                    __name__,
                    f"{self.instrumentation_id}/tested_versions/{package_name}",
                ) as f:
                    supported_versions = [
                        search(
                            _SPLIT_VERSION_FROM_COMMENT_PATTERN,
                            version_line.decode('utf-8').strip(),
                        ).group()
                        for version_line in f.readlines()
                        if not version_line.decode('utf-8').startswith("!")
                    ]

                    if distribution.version not in supported_versions:
                        raise UnsupportedDependencyVersionException(
                            package_name, distribution.version, supported_versions
                        )
                    else:
                        logger.debug(
                            "Package %s v %s supported for the %s instrumentation",
                            package_name,
                            distribution.version,
                            self.instrumentation_id,
                        )

            # Mark that we will suppress the upstream compatibility check
            compatibility_already_checked = True

        # Implementations of BaseInstrumentor have the very bad
        # habit of hard-requiring with 'import' clauses the
        # packages they instrument. For example, the 'pymysql'
        # package might be imported from 'opentelemetry.instrumentation.pymysql'.
        # Usually those hard imports are directly into the __init__, for extra FUN.
        # That is, effectively we may try to load code that does not exist in the
        # instrumented application as we instantiate the OpenTelemetry instrumentor.
        instrumentor: BaseInstrumentor = None
        try:
            instrumentor = self.get_otel_instrumentor()
        except ModuleNotFoundError as e:
            # This happens when the instrumentor imports directly a dependency
            # without guarding the import
            raise MissingDependencyException(e.name) from e
        except Exception as e:
            raise CannotInstantiateOpenTelemetryInstrumentor(
                "Cannot instantiate the OpenTelemetry instrumentor"
            ) from e

        if compatibility_already_checked:
            # Patch out the dependency conflict checks, we already verified or
            # were asked to suppress the check
            @patch_function_wrapper(
                instrumentor.__module__,
                f"{instrumentor.__class__.__name__}._check_dependency_conflicts",
            )
            def suppress_check_dependency_conflicts(wrapped, instance, args, kwargs):
                pass

        self._do_instrument(instrumentor)

    def _do_instrument(self, instrumentor: BaseInstrumentor, **kwargs):
        """Apply the instrumentation. May be subclasses to parse additionap parameters"""
        instrumentor.instrument()


class CannotInstantiateOpenTelemetryInstrumentor(Exception):
    def __init__(self, *args):
        super().__init__(args)


class MissingDependencyException(Exception):

    package_name: Optional[str] = None

    def __init__(self, package_name, *args):
        super().__init__(f"Package {package_name} not found", *args)
        self.package_name = package_name


class UnsupportedDependencyVersionException(Exception):

    package_name: Optional[str] = None
    version_found: Optional[str] = None
    supported_versions: Optional[List[str]] = None

    def __init__(self, package_name, version_found, supported_versions, *args):
        super().__init__(
            f"Incompatible version {version_found} found for the package {package_name}",
            *args,
        )
        self.package_name = package_name
        self.version_found = version_found
        self.supported_versions = supported_versions
