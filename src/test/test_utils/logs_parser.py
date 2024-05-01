from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

LOGS_FILE_FULL_PATH = os.environ.get("LUMIGO_DEBUG_LOGDUMP")


@dataclass(frozen=True)
class LogsContainer:
    def parse_logs_from_file(
        path: Optional[str] = LOGS_FILE_FULL_PATH,
    ) -> List[Dict[str, Any]]:
        with open(path) as file:
            return [json.loads(line) for line in file.readlines()]

    @staticmethod
    def get_logs_from_file(
        path: Optional[str] = LOGS_FILE_FULL_PATH,
        timeout_sec: int = 3,
        expected_log_count: int = 1,
    ) -> List[Dict[str, Any]]:
        waited_time_in_sec = 0

        while waited_time_in_sec < timeout_sec:
            try:
                logs = LogsContainer.parse_logs_from_file(path)
                if len(logs) >= expected_log_count:
                    return logs
            except Exception as err:
                print(
                    f"Failed to parse logs from file after {waited_time_in_sec}s: {err}"
                )
            time.sleep(1)
            waited_time_in_sec += 1

        return []
