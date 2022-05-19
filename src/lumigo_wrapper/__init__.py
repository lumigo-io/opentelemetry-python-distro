import os

if str(os.environ.get("LUMIGO_SWITCH_OFF")).lower() != "true":
    from .wrapper import lumigo_wrapper  # noqa
