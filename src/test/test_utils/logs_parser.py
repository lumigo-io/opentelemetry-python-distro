from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

LOGS_FILE_FULL_PATH = os.environ.get("LUMIGO_DEBUG_LOGDUMP")


@dataclass(frozen=True)
class LogsContainer:
    logs: List[Dict[str, Any]]

    def parse_logs_from_file(
        path: Optional[str] = LOGS_FILE_FULL_PATH,
    ) -> LogsContainer:
        with open(path) as file:
            return LogsContainer(logs=[json.loads(line) for line in file.readlines()])

    @staticmethod
    def get_logs_from_file(
        path: Optional[str] = LOGS_FILE_FULL_PATH,
        timeout_sec: int = 3,
        expected_log_count: int = 1,
    ) -> LogsContainer:
        waited_time_in_sec = 0
        logs_container = LogsContainer(logs=[])

        while waited_time_in_sec < timeout_sec:
            try:
                logs_container = LogsContainer.parse_logs_from_file(path)
                if len(logs_container) >= expected_log_count:
                    return logs_container
            except Exception as err:
                print(
                    f"Failed to parse logs from file after {waited_time_in_sec}s: {err}"
                )
            time.sleep(1)
            waited_time_in_sec += 1

        return logs_container

    def __len__(self) -> int:
        return len(self.logs)

    def __getitem__(self, key: int) -> Dict[str, Any]:
        return self.logs[key]
