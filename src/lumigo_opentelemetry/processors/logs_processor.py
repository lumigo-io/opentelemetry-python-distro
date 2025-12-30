from opentelemetry.sdk._logs import LogRecordProcessor, ReadWriteLogRecord


class LumigoLogRecordProcessor(LogRecordProcessor):
    def on_emit(self, log_record: ReadWriteLogRecord) -> None:
        # This class is used by __init__, so moving this to the enclosing scope will result in a circular import
        from lumigo_opentelemetry.libs.json_utils import dump

        log_record.log_record.body = dump(log_record.log_record.body)

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
