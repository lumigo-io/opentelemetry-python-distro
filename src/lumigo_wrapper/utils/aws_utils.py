from arnparse import arnparse


def is_arn(arn: str) -> bool:
    try:
        return bool(arnparse(arn))
    except Exception:
        return False


def get_resource_fullname(arn: str) -> str:
    return arnparse(arn).resource


def extract_region_from_arn(arn: str) -> str:
    return arnparse(arn).region
