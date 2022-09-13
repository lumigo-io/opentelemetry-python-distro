import unittest


class TestDistroInit(unittest.TestCase):
    def test_access_trace_provider(self):
        from lumigo_opentelemetry import tracer_provider

        self.assertIsNotNone(tracer_provider)

        self.assertTrue(hasattr(tracer_provider, 'force_flush'))
        self.assertTrue(hasattr(tracer_provider, 'shutdown'))