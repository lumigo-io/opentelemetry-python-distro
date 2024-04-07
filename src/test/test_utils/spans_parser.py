from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

SPANS_FILE_FULL_PATH = os.environ.get("LUMIGO_DEBUG_SPANDUMP")


class SpansCounter:
    counters = {}


spanCounter = SpansCounter()


@dataclass(frozen=True)
class SpansContainer:
    spans: List[Dict[str, Any]]

    @staticmethod
    def reset_spans_file(path: str = SPANS_FILE_FULL_PATH):
        """This empties an existing spans file, useful for local debugging"""
        open(path, "w").close()
        SpansContainer.update_span_offset(path)

    @staticmethod
    def update_span_offset(path: str = SPANS_FILE_FULL_PATH):
        spanCounter.counters[path] = sum(1 for _ in open(path))

    @staticmethod
    def get_span_offset(path: str = SPANS_FILE_FULL_PATH) -> int:
        return spanCounter.counters.get(path, 0)

    @staticmethod
    def parse_spans_from_file(
        path: Optional[str] = SPANS_FILE_FULL_PATH,
    ) -> SpansContainer:
        with open(path) as file:
            spans = [json.loads(line) for line in file.readlines()]

        return SpansContainer(spans=spans)

    @staticmethod
    def get_spans_from_file(
        path: Optional[str] = SPANS_FILE_FULL_PATH,
        wait_time_sec: int = 3,
        expected_span_count: int = 0,
    ) -> SpansContainer:
        spans = []
        waited_time_in_sec = 0
        span_offset = SpansContainer.get_span_offset(path)
        while waited_time_in_sec < wait_time_sec:
            try:
                spans = SpansContainer.parse_spans_from_file(path).spans
                if (
                    expected_span_count > 0
                    and len(spans) >= expected_span_count + span_offset
                ):
                    return SpansContainer(spans=spans[span_offset:])  # noqa
            except Exception as err:
                print(
                    f"Failed to parse spans from file after {waited_time_in_sec}s: {err}"
                )
            time.sleep(1)
            waited_time_in_sec += 1
        return SpansContainer(spans=spans[span_offset:] if spans else [])  # noqa

    def get_first_root(self) -> Optional[Dict[str, Any]]:
        root_spans = self.get_root_spans()
        return root_spans[0] if root_spans else None

    def get_root_spans(self) -> List[Dict[str, Any]]:
        return list(filter(lambda item: item["parent_id"] is None, self.spans))

    def get_children(self, root_span: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        root_span = self.get_first_root() if root_span is None else root_span
        return list(
            filter(
                lambda item: item["parent_id"] == root_span["context"]["span_id"],
                self.spans,
            )
        )

    def get_internals(self, root_span: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        return list(
            filter(
                lambda item: item["kind"] == "SpanKind.INTERNAL",
                self.get_children(root_span=root_span),
            )
        )

    def get_clients(self, root_span: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        return list(
            filter(
                lambda item: item["kind"] == "SpanKind.CLIENT",
                self.get_children(root_span=root_span),
            )
        )

    def find_child_span(self, predicate):
        for span in self.get_children():
            if predicate(span):
                yield span
                break

    def get_non_internal_children(
        self, name_filter: Optional[str] = None, root_span: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        children = [
            item
            for item in self.get_children(root_span=root_span)
            if item not in self.get_internals(root_span=root_span)
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
