from opentelemetry.sdk._logs import LogRecordProcessor, LogData


class LumigoLogRecordProcessor(LogRecordProcessor):
    def emit(self, log_data: LogData) -> None:
        # This class is used by __init__, so moving this to the enclosing scope will result in a circular import
        from lumigo_opentelemetry.libs.json_utils import dump

        log_data.log_record.body = dump(log_data.log_record.body)

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> None:
        pass
