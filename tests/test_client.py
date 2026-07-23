from __future__ import annotations

from typing import Any

import pytest

from epusdt import (
    APIError,
    EpusdtClient,
    HTTPError,
    InvalidNotifyURLError,
    ManualPaymentResponse,
    Network,
    OrderExistsError,
    OrderNotFoundError,
    OrderStatus,
    PaymentType,
    PublicConfig,
    RequestParamsError,
    SignatureError,
    SupportedAssetNotFoundError,
    Token,
    ValidationError,
    build_epay_type_selector,
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
    assert (
        call["kwargs"]["data"]["signature"]
        == "6f874b1919d95081835e2809b620e354a5866f5a6dbb2e432d1627f1eb10059d"
    )
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


def test_create_order_accepts_enum_values() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "trade_id": "TRADE_ENUM_001",
                        "order_id": "ORD_ENUM_001",
                        "amount": 100,
                        "currency": "CNY",
                        "actual_amount": 14.29,
                        "receive_address": "EQTestTonAddress001",
                        "token": "TON",
                        "status": 1,
                        "expiration_time": 1779530812,
                        "payment_url": "https://pay.example.com/pay/checkout-counter/TRADE_ENUM_001",
                    },
                    "request_id": "rid-enum",
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
        order_id="ORD_ENUM_001",
        amount=100,
        currency="cny",
        token=Token.TON,
        network=Network.TON,
        notify_url="https://merchant.example/notify",
    )

    payload = session.calls[0]["kwargs"]["json"]
    assert payload["token"] == "TON"
    assert payload["network"] == "ton"
    assert order.token == "TON"


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


def test_get_public_config_parses_official_supported_assets_variants() -> None:
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
                                "network": "polygon",
                                "display_name": "Polygon",
                                "tokens": ["USDT", "USDC", "USDC.e"],
                            },
                            {
                                "network": "ton",
                                "display_name": "TON",
                                "tokens": ["TON", "USDT"],
                            },
                            {
                                "network": "aptos",
                                "display_name": "Aptos",
                                "tokens": ["MOVEUSD", "USDT"],
                            },
                        ],
                        "site": {"cashier_name": "Acme Cashier"},
                        "epay": {"default_currency": "cny"},
                        "okpay": {"enabled": False, "allow_tokens": ["USDT"]},
                        "version": "v1.0.1",
                    },
                    "request_id": "rid-supported-assets",
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
    assert [asset.network for asset in config.supported_assets] == ["polygon", "ton", "aptos"]
    assert config.supported_assets[0].tokens == ["USDT", "USDC", "USDC.e"]
    assert config.supported_assets[1].tokens == ["TON", "USDT"]
    assert config.supported_assets[2].tokens == ["MOVEUSD", "USDT"]


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


def test_build_epay_type_selector_accepts_enums_and_strings() -> None:
    assert build_epay_type_selector(Token.USDT, Network.TRON) == "usdt.tron"
    assert build_epay_type_selector(" USDT ", " BINANCE ") == "usdt.binance"


def test_build_epay_type_selector_rejects_ambiguous_values() -> None:
    with pytest.raises(ValidationError):
        build_epay_type_selector("USDC.e", Network.POLYGON)


def test_build_epay_params_supports_type_selector_and_omitted_type() -> None:
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
    )
    selector = build_epay_type_selector(Token.USDT, Network.TRON)
    params = client.build_epay_params(
        out_trade_no="ORD_SELECTOR_001",
        money=100,
        notify_url="https://merchant.example/notify",
        type=selector,
    )
    assert params["type"] == "usdt.tron"
    assert params["sign"] == generate_epay_signature(
        {k: v for k, v in params.items() if k not in ("sign", "sign_type")},
        "secret",
    )

    omitted = client.build_epay_params(
        out_trade_no="ORD_SELECTOR_002",
        money=100,
        notify_url="https://merchant.example/notify",
        type=None,
    )
    assert "type" not in omitted
    assert omitted["sign"] == generate_epay_signature(
        {k: v for k, v in omitted.items() if k not in ("sign", "sign_type")},
        "secret",
    )


def test_create_order_accepts_custom_token_string() -> None:
    session = DummySession(
        [
            DummyResponse(
                200,
                json_data={
                    "status_code": 200,
                    "message": "success",
                    "data": {
                        "trade_id": "TRADE_CUSTOM_001",
                        "order_id": "ORD_CUSTOM_001",
                        "amount": 100,
                        "currency": "CNY",
                        "actual_amount": 14.29,
                        "receive_address": "0x1",
                        "token": "MOVEUSD",
                        "status": 1,
                        "expiration_time": 1779530812,
                        "payment_url": "https://pay.example.com/pay/checkout-counter/TRADE_CUSTOM_001",
                    },
                    "request_id": "rid-custom-token",
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
        order_id="ORD_CUSTOM_001",
        amount=100,
        currency="cny",
        token="MOVEUSD",
        network=Network.APTOS,
        notify_url="https://merchant.example/notify",
    )
    payload = session.calls[0]["kwargs"]["json"]
    assert payload["token"] == "MOVEUSD"
    assert payload["network"] == "aptos"
    assert order.token == "MOVEUSD"


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

    selector_payload = {
        "pid": "1000",
        "trade_no": "TRADE_SELECTOR_001",
        "out_trade_no": "ORD_SELECTOR_001",
        "type": "usdt.tron",
        "name": "VIP",
        "money": "100.0000",
        "trade_status": "TRADE_SUCCESS",
        "sign_type": "MD5",
    }
    selector_payload["sign"] = generate_epay_signature(selector_payload, "secret")
    selector_callback = client.parse_epay_callback(selector_payload)
    assert selector_callback.type == "usdt.tron"


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


def test_business_error_mapping_supports_supported_asset_not_found() -> None:
    session = DummySession(
        [
            DummyResponse(
                400,
                json_data={
                    "status_code": 10016,
                    "message": "supported asset not found",
                    "data": None,
                    "request_id": "rid-10016",
                },
                text='{"status_code":10016}',
            )
        ]
    )
    client = EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="secret",
        session=session,
    )
    with pytest.raises(SupportedAssetNotFoundError) as exc:
        client.get_checkout("TRADE001")
    assert exc.value.business_code == 10016
    assert exc.value.request_id == "rid-10016"


def test_top_level_exception_exports() -> None:
    assert issubclass(HTTPError, Exception)
    assert issubclass(SupportedAssetNotFoundError, APIError)


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
