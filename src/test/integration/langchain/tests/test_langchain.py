import os
import sys
import unittest
from os import path

import subprocess



class TestFlaskSpans(unittest.TestCase):
    sample_path = path.join(
        path.dirname(path.abspath(__file__)),
        f"../app/app.py",
    )
    subprocess.check_output(
        [sys.executable, sample_path],
        env={
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": f"langchain-app",
        },
    )