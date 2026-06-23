from __future__ import annotations

from typing import Any

import pytest

from epusdt import (
    APIError,
    EpusdtClient,
    InvalidNotifyURLError,
    ManualPaymentResponse,
    OrderExistsError,
    OrderNotFoundError,
    OrderStatus,
    PaymentType,
    PublicConfig,
    RequestParamsError,
    SignatureError,
    ValidationError,
    generate_epay_signature,
    generate_gmpay_signature,
)


class DummyResponse:
    def __init__(
        self,
        status_code: int,
        *,
        json_data: Any = None,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("no json data")
        return self._json_data


class DummySession:
    def __init__(self, responses: list[DummyResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []
        self.headers: dict[str, str] = {}
        self.closed = False

    def request(self, method: str, url: str, timeout: float, **kwargs: Any) -> DummyResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


def test_create_order_form_payload() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "trade_id": "20260523171652123456001",
                        "order_id": "ORD202605230001",
                        "amount": 100,
                        "currency": "CNY",
                        "actual_amount": 14.29,
                        "receive_address": "TTestTronAddress001",
                        "token": "USDT",
                        "status": 1,
                        "expiration_time": 1779530812,
                        "payment_url": "https://pay.example.com/pay/checkout-counter/20260523171652123456001",
                    },
                    "request_id": "rid-1",
                },
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
        session=session,
    )
    order = client.create_order(
        order_id="ORD202605230001",
        amount=100,
        currency="cny",
        token="usdt",
        network="tron",
        notify_url="https://merchant.example/notify",
        redirect_url="https://merchant.example/return",
        name="VIP",
        use_form=True,
    )

    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/payments/gmpay/v1/order/create-transaction")
    assert call["kwargs"]["data"]["signature"] == "476412c422f4dd75c3d533f5c47a9cac"
    assert order.status is OrderStatus.WAITING_PAYMENT


def test_create_order_accepts_string_amount_and_string_status_code() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": "200",
                    "message": "success",
                    "data": {
                        "trade_id": "TRADE002",
                        "order_id": "ORD002",
                        "amount": "100.50",
                        "currency": "CNY",
                        "actual_amount": "14.29",
                        "receive_address": "TTestTronAddress002",
                        "token": "USDT",
                        "status": 1,
                        "expiration_time": 1779530812,
                        "payment_url": "https://pay.example.com/pay/checkout-counter/TRADE002",
                    },
                    "request_id": "rid-amount",
                },
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    order = client.create_order(
        order_id="ORD002",
        amount="100.50",
        currency="cny",
        notify_url="https://merchant.example/notify",
    )
    assert session.calls[0]["kwargs"]["json"]["amount"] == 100.5
    assert order.amount == 100.5


def test_get_public_config_parsing() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "supported_assets": [
                            {
                                "network": "tron",
                                "display_name": "TRON",
                                "tokens": ["TRX", "USDT"],
                            }
                        ],
                        "site": {"cashier_name": "Acme Cashier"},
                        "epay": {"default_currency": "cny"},
                        "okpay": {"enabled": False, "allow_tokens": ["USDT"]},
                        "version": "v1.0.1",
                    },
                    "request_id": "rid-2",
                },
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    config = client.get_public_config()
    assert isinstance(config, PublicConfig)
    assert config.supported_assets[0].network == "tron"
    assert config.site.cashier_name == "Acme Cashier"


def test_create_epay_order_returns_redirect() -> None:
    session = DummySession(
        [
            DummyResponse(
                302,
                text="",
                headers={"Location": "/pay/checkout-counter/20260523171652123456001"},
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
        session=session,
    )
    redirect = client.create_epay_order(
        out_trade_no="ORD202605230001",
        money=100,
        notify_url="https://merchant.example/notify",
        return_url="https://merchant.example/return",
        name="VIP",
    )
    assert redirect.status_code == 302
    assert redirect.location == "/pay/checkout-counter/20260523171652123456001"
    assert redirect.checkout_url == "https://pay.example.com/pay/checkout-counter/20260523171652123456001"


def test_base_url_accepts_full_epay_submit_url() -> None:
    client = EpusdtClient(
        base_url="https://pay.example.com/gateway/payments/epay/v1/order/create-transaction/submit.php",
        pid="1000",
        secret_key="secret",
    )
    assert client.base_url == "https://pay.example.com/gateway"


def test_context_manager_does_not_close_external_session() -> None:
    session = DummySession([])
    with EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    ) as client:
        assert client.base_url == "https://pay.example.com"
    assert session.closed is False


def test_callback_parsing_and_signature_verification() -> None:
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
    )
    gmpay_payload = {
        "pid": "1000",
        "trade_id": "TRADE001",
        "order_id": "ORD001",
        "amount": 100,
        "actual_amount": 14.29,
        "receive_address": "addr",
        "token": "USDT",
        "block_transaction_id": "0xabc",
        "status": 2,
    }
    gmpay_payload["signature"] = generate_gmpay_signature(gmpay_payload, "secret")
    callback = client.parse_gmpay_callback(gmpay_payload)
    assert callback.status is OrderStatus.PAID

    epay_payload = {
        "pid": "1000",
        "trade_no": "TRADE001",
        "out_trade_no": "ORD001",
        "type": "alipay",
        "name": "VIP",
        "money": "100.0000",
        "trade_status": "TRADE_SUCCESS",
        "sign_type": "MD5",
    }
    epay_payload["sign"] = generate_epay_signature(epay_payload, "secret")
    epay = client.parse_epay_callback(epay_payload)
    assert epay.trade_status.value == "TRADE_SUCCESS"


def test_invalid_callback_signature_raises() -> None:
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
    )
    payload = {
        "pid": "1000",
        "trade_id": "TRADE001",
        "order_id": "ORD001",
        "amount": 100,
        "actual_amount": 14.29,
        "receive_address": "addr",
        "token": "USDT",
        "block_transaction_id": "0xabc",
        "status": 2,
        "signature": "bad",
    }
    with pytest.raises(SignatureError):
        client.parse_gmpay_callback(payload)


def test_epay_mode_requires_numeric_pid() -> None:
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="merchant-a",
        secret_key="secret",
    )
    with pytest.raises(ValidationError):
        client.build_epay_params(
            out_trade_no="ORD001",
            money=100,
            notify_url="https://merchant.example/notify",
        )
    with pytest.raises(ValidationError):
        client.create_order(
            order_id="ORD001",
            amount=100,
            currency="cny",
            notify_url="https://merchant.example/notify",
            payment_type="Epay",
        )


def test_create_epay_order_raises_api_error_on_json_failure() -> None:
    session = DummySession(
        [
            DummyResponse(
                400,
                json_data={
                    "status_code": 10009,
                    "message": "params error",
                    "data": None,
                    "request_id": "rid-4",
                },
                text='{"status_code":10009,"message":"params error"}',
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    with pytest.raises(APIError) as exc:
        client.create_epay_order(
            out_trade_no="ORD001",
            money=100,
            notify_url="https://merchant.example/notify",
        )
    assert exc.value.business_code == 10009
    assert exc.value.request_id == "rid-4"


@pytest.mark.parametrize(
    ("business_code", "exc_type"),
    [
        (10002, OrderExistsError),
        (10008, OrderNotFoundError),
        (10009, RequestParamsError),
        (10041, InvalidNotifyURLError),
    ],
)
def test_business_error_maps_to_specific_exception(
    business_code: int,
    exc_type: type[APIError],
) -> None:
    session = DummySession(
        [
            DummyResponse(
                400,
                json_data={
                    "status_code": business_code,
                    "message": "mapped error",
                    "data": None,
                    "request_id": "rid-map",
                },
                text='{"status_code":400}',
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    with pytest.raises(exc_type) as exc:
        client.get_checkout("TRADE001")
    assert exc.value.business_code == business_code
    assert exc.value.request_id == "rid-map"


def test_checkout_model_parses_payment_type() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "trade_id": "TRADE001",
                        "amount": 100,
                        "actual_amount": 14.29,
                        "token": "USDT",
                        "currency": "CNY",
                        "receive_address": "addr",
                        "network": "tron",
                        "status": 1,
                        "payment_type": "gmpay",
                        "expiration_time": 1779530812000,
                        "redirect_url": "https://merchant.example/return",
                        "payment_url": "",
                        "created_at": 1779530212000,
                        "is_selected": False,
                    },
                    "request_id": "rid-3",
                },
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    checkout = client.get_checkout("TRADE001")
    assert checkout.payment_type is PaymentType.GMPAY


def test_submit_tx_hash() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "trade_id": "TRADE001",
                        "status": 2,
                        "block_transaction_id": "0xabc123",
                    },
                    "request_id": "rid-5",
                },
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    result = client.submit_tx_hash(trade_id="TRADE001", block_transaction_id="0xabc123")
    assert isinstance(result, ManualPaymentResponse)
    assert result.status is OrderStatus.PAID
