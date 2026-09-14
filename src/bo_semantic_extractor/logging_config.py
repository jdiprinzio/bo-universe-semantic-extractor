"""Structured logging with automatic secret redaction.

HTTP request/response bodies are never logged by default. Authorization/Cookie/Set-Cookie
headers and password/token/secret-shaped content are redacted from every log record before
it reaches a handler.
"""

from __future__ import annotations

import logging
import re
from typing import Any

REDACTED = "***REDACTED***"

_HEADER_NAMES_TO_REDACT = {"authorization", "cookie", "set-cookie"}

_HEADER_LINE_PATTERN = re.compile(r"(?i)\b(authorization|cookie|set-cookie)\s*:\s*.+")

_SECRET_KEYVALUE_PATTERN = re.compile(
    r"(?i)\b(password|token|secret|client_secret|api[_-]?key)\b\s*=\s*([^\s,;&\"']+)"
)


def redact_text(text: str) -> str:
    """Redact common secret patterns (headers, password=, token=, secret=) from a log line."""
    text = _HEADER_LINE_PATTERN.sub(lambda m: f"{m.group(1)}: {REDACTED}", text)
    return _SECRET_KEYVALUE_PATTERN.sub(lambda m: f"{m.group(1)}={REDACTED}", text)


def redact_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of an HTTP header mapping with sensitive headers redacted."""
    return {
        key: (REDACTED if key.lower() in _HEADER_NAMES_TO_REDACT else value)
        for key, value in headers.items()
    }


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secret-like content from every log record message."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: redact_text(value) if isinstance(value, str) else value
                    for key, value in record.args.items()
                }
            else:
                record.args = tuple(
                    redact_text(arg) if isinstance(arg, str) else arg for arg in record.args
                )
        return True


_configured = False


def configure_logging(level: str = "INFO", *, log_http_bodies: bool = False) -> None:
    """Configure root logging with structured output and secret redaction.

    `log_http_bodies` defaults to `False`: HTTP request/response bodies are never logged
    unless explicitly enabled, and this pipeline never enables it against a live
    BusinessObjects system.
    """
    global _configured
    root = logging.getLogger()
    root.setLevel(level.upper())
    if not _configured:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        handler.addFilter(RedactingFilter())
        root.addHandler(handler)
        _configured = True
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING if not log_http_bodies else logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
