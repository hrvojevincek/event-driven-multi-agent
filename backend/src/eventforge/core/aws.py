from typing import Any

import boto3
from botocore.config import Config

from eventforge.core.config import Settings

BOTO_CONNECT_TIMEOUT_SECONDS = 5
BOTO_READ_TIMEOUT_SECONDS = 25


def boto_client(service_name: str, settings: Settings) -> Any:
    kwargs: dict[str, Any] = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "config": Config(
            connect_timeout=BOTO_CONNECT_TIMEOUT_SECONDS,
            read_timeout=BOTO_READ_TIMEOUT_SECONDS,
        ),
    }
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client(service_name, **kwargs)
