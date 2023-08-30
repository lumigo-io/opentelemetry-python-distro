import time


def wait_for_exporter(wait_time_sec: int = 3):
    """Wait for the exporter to have collected all the spans."""

    # TODO Do something deterministic
    time.sleep(wait_time_sec)  # Sleep to allow the exporter to catch up
