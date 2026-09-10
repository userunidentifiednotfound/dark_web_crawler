"""Structured JSON / text logging for high observability."""

from datetime import datetime
import json
import logging
import sys
from dwi_crawler.config.settings import get_settings


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include custom fields if present
        for attr in ("worker_id", "job_id", "company_id", "url_hash", "event", "duration", "status", "error"):
            if hasattr(record, attr):
                data[attr] = getattr(record, attr)
        return json.dumps(data)


def setup_logging(structured: bool = False) -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    # Clean existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if structured:
        handler.setFormatter(StructuredLogFormatter())
    else:
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(fmt)

    root.addHandler(handler)
