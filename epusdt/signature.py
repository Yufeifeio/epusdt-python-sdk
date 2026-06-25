from __future__ import annotations

import hashlib
import hmac
import math
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, MutableMapping, Optional, Sequence

from .exceptions import ValidationError


def _decimal_to_string(value: Decimal) -> str:
    if not value.is_finite():
        raise ValidationError("numeric values used for signatures must be finite")
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return format(normalized.quantize(Decimal("1")), "f")
    text = format(normalized, "f")
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _signature_value(value: Any) -> Optional[str]:
    if isinstance(value, Enum):
        return _signature_value(value.value)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValidationError("boolean values are not supported in epusdt signatures")
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError("float values used for signatures must be finite")
        return _decimal_to_string(Decimal(str(value)))
    if isinstance(value, Decimal):
        return _decimal_to_string(value)
    raise ValidationError(f"unsupported signature value type: {type(value).__name__}")


def _build_signing_string(params: Mapping[str, Any], excluded: Sequence[str]) -> str:
    excluded_set = set(excluded)
    parts = []
    for key in params.keys():
        if key in excluded_set:
            continue
        value = _signature_value(params[key])
        if value in (None, ""):
            continue
        parts.append(f"{key}={value}")
    parts.sort()
    return "&".join(parts)


def build_gmpay_signing_string(params: Mapping[str, Any]) -> str:
    return _build_signing_string(params, excluded=("signature",))


def build_epay_signing_string(params: Mapping[str, Any]) -> str:
    return _build_signing_string(params, excluded=("sign", "sign_type"))


def generate_gmpay_signature(params: Mapping[str, Any], secret_key: str) -> str:
    sign_str = build_gmpay_signing_string(params) + secret_key
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().lower()  # nosec B324


def generate_epay_signature(params: Mapping[str, Any], secret_key: str) -> str:
    sign_str = build_epay_signing_string(params) + secret_key
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().lower()  # nosec B324


def _extract_signature(
    params: Mapping[str, Any],
    explicit_signature: Optional[str],
    field: str,
) -> Optional[str]:
    if explicit_signature is not None:
        return explicit_signature
    raw = params.get(field)
    if raw is None:
        return None
    extracted = _signature_value(raw)
    return extracted or None


def verify_gmpay_signature(
    params: Mapping[str, Any],
    secret_key: str,
    signature: Optional[str] = None,
) -> bool:
    received = _extract_signature(params, signature, "signature")
    if not received:
        return False
    expected = generate_gmpay_signature(params, secret_key)
    return hmac.compare_digest(expected, received)


def verify_epay_signature(
    params: Mapping[str, Any],
    secret_key: str,
    sign: Optional[str] = None,
) -> bool:
    received = _extract_signature(params, sign, "sign")
    if not received:
        return False
    expected = generate_epay_signature(params, secret_key)
    return hmac.compare_digest(expected, received)


def stringify_params(params: Mapping[str, Any]) -> MutableMapping[str, str]:
    result: MutableMapping[str, str] = {}
    for key, value in params.items():
        serialized = _signature_value(value)
        if serialized is None:
            continue
        result[key] = serialized
    return result
