from .. import AbstractInstrumentor

class PyramidInstrumentor(AbstractInstrumentor):

    def __init__(self):
        super().__init__("pyramid")

    def check_if_applicable(self):
        import pyramid.config  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        PyramidInstrumentor().instrument()

instrumentor = PyramidInstrumentor()
