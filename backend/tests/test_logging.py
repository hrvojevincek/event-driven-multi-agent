import json
import logging

from eventforge.core.config import Settings
from eventforge.core.logging import JsonFormatter, setup_logging


def test_setup_logging_uses_json_formatter_outside_local() -> None:
    settings = Settings(environment="production", log_level="WARNING")
    setup_logging(settings)

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert root.level == logging.WARNING


def test_setup_logging_uses_pretty_formatter_in_local() -> None:
    settings = Settings(environment="local", log_level="INFO")
    setup_logging(settings)

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert not isinstance(root.handlers[0].formatter, JsonFormatter)


def test_json_formatter_outputs_structured_log() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="eventforge.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "eventforge.test"
    assert payload["message"] == "hello"
    assert "timestamp" in payload
