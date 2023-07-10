import os

SHOULD_INSTRUMENT_PAYLOADS = (
    os.getenv("LUMIGO_INSTRUMENT_GRPC_PAYLOADS", "true").lower() != "false"
)
PAYLOAD_MAX_SIZE = 4095
