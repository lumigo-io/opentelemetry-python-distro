from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


SPANS_FILE_FULL_PATH = os.environ["LUMIGO_DEBUG_SPANDUMP"]


class SpansCounter:
    counter = 0


spanCounter = SpansCounter()


@dataclass(frozen=True)
class SpansContainer:
    spans: List[Dict[str, Any]]

    @staticmethod
    def increment_spans():
        spanCounter.counter = sum(1 for line in open(SPANS_FILE_FULL_PATH))

    @staticmethod
    def parse_spans_from_file() -> SpansContainer:
        with open(SPANS_FILE_FULL_PATH) as file:
            spans = [json.loads(line) for line in file.readlines()]

        return SpansContainer(spans=spans)

    @staticmethod
    def get_spans_from_file() -> SpansContainer:
        spans = SpansContainer.parse_spans_from_file().spans
        return SpansContainer(spans=spans[spanCounter.counter :])  # noqa

    def get_root(self) -> Dict[str, Any]:
        return list(filter(lambda item: item["parent_id"] is None, self.spans))[0]

    def get_children(self) -> List[Dict[str, Any]]:
        return list(
            filter(
                lambda item: item["parent_id"] == self.get_root()["context"]["span_id"],
                self.spans,
            )
        )

    def get_internals(self) -> List[Dict[str, Any]]:
        return list(
            filter(
                lambda item: item["kind"] == "SpanKind.INTERNAL", self.get_children()
            )
        )

    def get_non_internal_children(
        self, name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        children = [
            item for item in self.get_children() if item not in self.get_internals()
        ]
        if not name_filter:
            return children
        return [child for child in children if child["name"] == name_filter]

    @staticmethod
    def get_attribute_from_list_of_spans(
        list_of_spans: List[Dict[str, Any]], attribute_name: str
    ) -> Any:
        return list(
            filter(
                lambda item: item["attributes"].get(attribute_name) is not None,
                list_of_spans,
            )
        )[0]["attributes"][attribute_name]
