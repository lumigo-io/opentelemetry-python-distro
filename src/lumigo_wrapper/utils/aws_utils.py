def get_resource_fullname(arn: str) -> str:
    return arn.split(":", 5)[5]


def extract_region_from_arn(arn: str) -> str:
    return arn.split(":", 5)[3]
