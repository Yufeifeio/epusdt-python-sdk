from __future__ import annotations

from typing import Any, Optional


class EpusdtError(Exception):
    """Base exception for this SDK."""


class ValidationError(EpusdtError):
    """Raised when user input is invalid before the request is sent."""


class SignatureError(EpusdtError):
    """Raised when callback signature verification fails."""


class NetworkError(EpusdtError):
    """Raised when the request cannot reach the gateway."""


class RequestTimeoutError(EpusdtError):
    """Raised when the gateway request times out."""


class HTTPError(EpusdtError):
    """Base class for raw HTTP failures."""

    def __init__(
        self,
        message: str,
        *,
        http_status: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.response_text = response_text


class ClientError(HTTPError):
    """Raised for non-auth client-side HTTP errors."""


class AuthenticationError(ClientError):
    """Raised when the gateway rejects credentials or signature."""


class ServerError(HTTPError):
    """Raised for retryable 5xx gateway errors."""


class APIError(EpusdtError):
    """Raised when the gateway returns a business error payload."""

    def __init__(
        self,
        message: str,
        *,
        business_code: Optional[int] = None,
        http_status: Optional[int] = None,
        response: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.business_code = business_code
        self.http_status = http_status
        self.response = response

