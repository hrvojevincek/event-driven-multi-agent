import json
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from eventforge.core.aws import boto_client
from eventforge.core.config import Settings, get_settings


def send_task_success(
    task_token: str,
    output: dict[str, Any],
    settings: Settings | None = None,
) -> None:
    """Notify Step Functions that a waitForTaskToken step succeeded."""
    client = boto_client("stepfunctions", settings or get_settings())
    try:
        client.send_task_success(
            taskToken=task_token,
            output=json.dumps(output, default=str),
        )
    except (BotoCoreError, ClientError) as exc:
        msg = "Step Functions SendTaskSuccess failed"
        raise RuntimeError(msg) from exc


def send_task_failure(
    task_token: str,
    error: str,
    cause: str,
    settings: Settings | None = None,
) -> None:
    """Notify Step Functions that a waitForTaskToken step failed."""
    client = boto_client("stepfunctions", settings or get_settings())
    try:
        client.send_task_failure(taskToken=task_token, error=error, cause=cause)
    except (BotoCoreError, ClientError) as exc:
        msg = "Step Functions SendTaskFailure failed"
        raise RuntimeError(msg) from exc
