"""Stable error categories for BusinessObjects client and pipeline operations.

Error messages must never leak secrets (tokens, passwords, cookies, client secrets).
"""

from __future__ import annotations


class BoClientError(Exception):
    """Base class for all BusinessObjects client errors. Carries a stable `error_code`."""

    error_code: str = "API_CONTRACT_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(BoClientError):
    error_code = "CONFIG_ERROR"


class AuthenticationError(BoClientError):
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(BoClientError):
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(BoClientError):
    error_code = "NOT_FOUND"


class AmbiguousMatchError(BoClientError):
    error_code = "AMBIGUOUS_MATCH"


class ApiContractError(BoClientError):
    error_code = "API_CONTRACT_ERROR"


class PaginationError(BoClientError):
    error_code = "PAGINATION_ERROR"


class RateLimitedError(BoClientError):
    error_code = "RATE_LIMITED"


class SdkUnavailableError(BoClientError):
    """Raised when a required endpoint/operation has not been configured or confirmed.

    Used instead of guessing an unconfirmed SAP REST endpoint path.
    """

    error_code = "SDK_UNAVAILABLE"
