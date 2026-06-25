from __future__ import annotations

import pytest

from epusdt.exceptions import (
    APIError,
    AuthenticationError,
    ChainNotEnabledError,
    ClientError,
    HTTPError,
    InvalidNotifyURLError,
    InvalidRedirectURLError,
    InvalidAmountError,
    ManualPaymentProviderError,
    ManualPaymentVerifyError,
    OrderApiKeyUnavailableError,
    OrderExistsError,
    OrderNotAwaitingPaymentError,
    OrderNotFoundError,
    OrderStatusChangedError,
    PaymentProviderConfigError,
    PaymentProviderCreateError,
    PaymentProviderNotEnabledError,
    PaymentProviderUnsupportedError,
    RateCalculationError,
    RequestParamsError,
    SubOrderLimitExceededError,
    SubOrderSwitchNotAllowedError,
    SupportedAssetNotFoundError,
    SystemAPIError,
    TransactionAlreadyProcessedError,
    create_api_error,
    ERROR_CODE_MAP,
    EPayReturnSignatureBuildError,
    NoAvailableAmountChannelError,
    NoAvailableWalletError,
)


@pytest.mark.parametrize(
    ("code", "exc_type"),
    [
        (400, SystemAPIError),
        (10002, OrderExistsError),
        (10003, NoAvailableWalletError),
        (10004, InvalidAmountError),
        (10005, NoAvailableAmountChannelError),
        (10006, RateCalculationError),
        (10007, TransactionAlreadyProcessedError),
        (10008, OrderNotFoundError),
        (10009, RequestParamsError),
        (10010, OrderStatusChangedError),
        (10011, SubOrderLimitExceededError),
        (10012, SubOrderSwitchNotAllowedError),
        (10013, OrderNotAwaitingPaymentError),
        (10014, ChainNotEnabledError),
        (10016, SupportedAssetNotFoundError),
        (10017, PaymentProviderNotEnabledError),
        (10018, PaymentProviderConfigError),
        (10019, PaymentProviderUnsupportedError),
        (10038, ManualPaymentVerifyError),
        (10039, ManualPaymentProviderError),
        (10041, InvalidNotifyURLError),
        (10042, PaymentProviderCreateError),
        (10044, InvalidRedirectURLError),
        (10045, OrderApiKeyUnavailableError),
        (10046, EPayReturnSignatureBuildError),
    ],
)
def test_error_code_map_resolves_specific_types(code: int, exc_type: type) -> None:
    exc = create_api_error("boom", business_code=code, http_status=400, request_id="r1")
    assert isinstance(exc, ERROR_CODE_MAP[code])
    assert isinstance(exc, APIError)
    assert exc.business_code == code
    assert exc.http_status == 400
    assert exc.request_id == "r1"


def test_unknown_code_falls_back_to_apierror() -> None:
    exc = create_api_error("boom", business_code=99999)
    assert type(exc) is APIError


def test_none_code_falls_back_to_apierror() -> None:
    exc = create_api_error("boom", business_code=None)
    assert type(exc) is APIError


def test_exception_hierarchy() -> None:
    assert issubclass(AuthenticationError, ClientError)
    assert issubclass(ClientError, HTTPError)
    assert issubclass(SystemAPIError, APIError)
    assert issubclass(OrderExistsError, APIError)


def test_http_error_carries_status_and_text() -> None:
    err = HTTPError("oops", http_status=502, response_text="bad gateway")
    assert err.http_status == 502
    assert err.response_text == "bad gateway"


def test_api_error_does_not_leak_secret_in_str() -> None:
    err = create_api_error("order exists", business_code=10002, response={"x": 1})
    assert "secret" not in str(err).lower()
