import json
from typing import Any


def parse_eventbridge_sqs_body(body: str) -> dict[str, Any]:
    """Extract EventBridge detail from an SQS message body."""
    wrapper = json.loads(body)
    detail = wrapper["detail"]
    if isinstance(detail, str):
        return json.loads(detail)
    return detail
