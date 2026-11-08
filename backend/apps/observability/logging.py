"""Logging building blocks: request-id context, filter and JSON formatter."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

NO_REQUEST_ID = "-"

request_id_var: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)

# Attributes every LogRecord has; anything else was passed through `extra`.
_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime", "taskName"}


class RequestIdFilter(logging.Filter):
    """Adds `request_id` to every record, "-" outside of a request."""

    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Formats each record as a single-line JSON object."""

    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
