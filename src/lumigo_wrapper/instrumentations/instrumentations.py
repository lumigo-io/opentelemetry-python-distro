from __future__ import annotations

from enum import Enum
from typing import List

frameworks: List[Framework] = []


class Framework(Enum):
    Flask = "flask"
    FastAPI = "fast-api"
    Django = "django"
    Unknown = "unknown"
