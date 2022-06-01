import json
import requests
import time
import unittest


class TestFastApiSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:8000/")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"message": "Hello FastAPI!"})

        # TODO Do something deterministic
        time.sleep(2)  # Sleep for two seconds to allow the exporter to catch up

        with open("spans.txt") as file:
            spans = [json.loads(line) for line in file.readlines()]

        self.assertEqual(3, len(spans))
