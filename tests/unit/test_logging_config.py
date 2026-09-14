"""Unit tests for logging redaction helpers."""

from __future__ import annotations

from bo_semantic_extractor.logging_config import redact_headers, redact_text


def test_redact_text_redacts_password_field() -> None:
    text = "Login attempt with password=hunter2 for user bob"
    assert "hunter2" not in redact_text(text)


def test_redact_text_redacts_authorization_header_like_content() -> None:
    text = "Authorization: Bearer abc123"
    redacted = redact_text(text)
    assert "abc123" not in redacted


def test_redact_text_redacts_token_and_secret() -> None:
    text = "token=abc secret=def"
    redacted = redact_text(text)
    assert "abc" not in redacted
    assert "def" not in redacted


def test_redact_headers_masks_sensitive_headers_only() -> None:
    headers = {
        "Authorization": "Bearer abc",
        "Cookie": "sid=1",
        "Content-Type": "application/json",
    }
    redacted = redact_headers(headers)
    assert redacted["Authorization"] != "Bearer abc"
    assert redacted["Cookie"] != "sid=1"
    assert redacted["Content-Type"] == "application/json"
