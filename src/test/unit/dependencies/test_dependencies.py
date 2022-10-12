from unittest import TestCase
from unittest.mock import patch

from json import loads
from os import environ

from lumigo_opentelemetry import init


class TestDependencyReport(TestCase):
    @patch("lumigo_opentelemetry.dependencies.report")
    @patch.dict(
        environ, {"LUMIGO_TRACER_TOKEN": "", "LUMIGO_REPORT_DEPENDENCIES": "true"}
    )
    def test_dependency_report_disabled_if_no_lumigo_token(self, report_mock):
        assert not environ.get("LUMIGO_TRACER_TOKEN")

        init()

        assert not report_mock.called

    @patch("lumigo_opentelemetry.dependencies.report")
    @patch.dict(
        environ,
        {"LUMIGO_TRACER_TOKEN": "abcdef", "LUMIGO_REPORT_DEPENDENCIES": "false"},
    )
    def test_dependency_report_disabled_if_lumigo_report_dependencies_false(
        self, report_mock
    ):
        init()

        assert not report_mock.called

    @patch("lumigo_opentelemetry.dependencies.report")
    @patch.dict(
        environ,
        {
            "LUMIGO_TRACER_TOKEN": "abcdef",
            "LUMIGO_REPORT_DEPENDENCIES": "true",
            "LUMIGO_ENDPOINT": "https://some.url",
        },
    )
    def test_dependency_report_disabled_if_lumigo_endpoint_not_default(
        self, report_mock
    ):
        init()

        assert not report_mock.called

    @patch("lumigo_opentelemetry.dependencies._report_to_saas")
    @patch.dict(
        environ, {"LUMIGO_TRACER_TOKEN": "abcdef", "LUMIGO_REPORT_DEPENDENCIES": "true"}
    )
    def test_dependency_report_called(self, report_to_saas_mock):
        init()

        assert report_to_saas_mock.call_count == 1

        [url, lumigo_token, data] = report_to_saas_mock.call_args.args

        assert url == "https://ga-otlp.lumigo-tracer-edge.golumigo.com/v1/dependencies"
        assert lumigo_token == "abcdef"

        parsed_data = loads(data)
        resource_attributes = parsed_data["resourceAttributes"]
        dependencies = parsed_data["dependencies"]

        assert resource_attributes and resource_attributes["lumigo.distro.version"]
        assert "process.environ" not in resource_attributes.keys()
        assert dependencies and len(dependencies) > 0
