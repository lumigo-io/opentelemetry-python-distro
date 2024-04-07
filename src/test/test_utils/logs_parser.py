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

    @staticmethod
    def get_logs_from_file(
        path: Optional[str] = LOGS_FILE_FULL_PATH,
        wait_time_sec: int = 3,
    ) -> LogsContainer:
        time.sleep(wait_time_sec)

        try:
            with open(path) as file:
                logs = [json.loads(line) for line in file.readlines()]

            return LogsContainer(logs=logs)

        except Exception as err:
            print(f"Failed to parse logs from file after {wait_time_sec}s: {err}")

        return LogsContainer(logs=[])

    def __len__(self) -> int:
        return len(self.logs)

    def __getitem__(self, item) -> Dict[str, Any]:
        return self.logs[item]
