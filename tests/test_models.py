from __future__ import annotations

import pytest

from epusdt import (
    CheckoutOrder,
    CheckStatusResponse,
    CreateOrderResponse,
    EpayCallback,
    GmpayCallback,
    ManualPaymentResponse,
    Network,
    OrderStatus,
    PaymentType,
    PublicConfig,
    Token,
    TradeStatus,
)
from epusdt.models import EpayDefaults, OkpayConfig, SiteConfig, SupportedAsset


def test_create_order_response_datetime_property() -> None:
    order = CreateOrderResponse(
        trade_id="TRADE001",
        order_id="ORD001",
        amount=100,
        currency="CNY",
        actual_amount=14.29,
        receive_address="addr",
        token="USDT",
        status=OrderStatus.WAITING_PAYMENT,
        expiration_time=1779530812,
        payment_url="https://pay.example.com/pay/checkout-counter/TRADE001",
    )
    assert order.expiration_datetime.year >= 2026


def test_checkout_order_datetime_properties() -> None:
    checkout = CheckoutOrder(
        trade_id="TRADE001",
        amount=100,
        actual_amount=14.29,
        token="USDT",
        currency="CNY",
        receive_address="addr",
        network="tron",
        status=OrderStatus.WAITING_PAYMENT,
        payment_type=PaymentType.GMPAY,
        expiration_time=1779530812000,
        redirect_url="https://merchant.example/return",
        payment_url="",
        created_at=1779530212000,
        is_selected=False,
        server_time=1779530213000,
    )
    assert checkout.expiration_datetime.year >= 2026
    assert checkout.created_datetime.year >= 2026
    assert checkout.server_datetime.year >= 2026
    assert checkout.server_time == 1779530213000


def test_checkout_order_from_dict_parses_server_time_default() -> None:
    checkout = CheckoutOrder.from_dict(
        {
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
            "server_time": 1779530213000,
            "is_selected": False,
        }
    )
    assert checkout.server_time == 1779530213000

    older = CheckoutOrder.from_dict(
        {
            "trade_id": "TRADE002",
            "amount": 100,
            "actual_amount": 14.29,
            "token": "USDT",
            "currency": "CNY",
            "receive_address": "addr",
            "network": "tron",
            "status": 1,
            "payment_type": "gmpay",
            "expiration_time": 1779530812000,
            "redirect_url": "",
            "payment_url": "",
            "created_at": 1779530212000,
            "is_selected": False,
        }
    )
    assert older.server_time == 0


def test_official_network_and_token_enums() -> None:
    assert Network.TRON.value == "tron"
    assert Network.SOLANA.value == "solana"
    assert Network.ETHEREUM.value == "ethereum"
    assert Network.BSC.value == "binance"
    assert Network.POLYGON.value == "polygon"
    assert Network.PLASMA.value == "plasma"
    assert Network.TON.value == "ton"
    assert Network.APTOS.value == "aptos"

    assert Token.USDT.value == "USDT"
    assert Token.TRX.value == "TRX"
    assert Token.USDC.value == "USDC"
    assert Token.USDC_E.value == "USDC.e"
    assert Token.SOL.value == "SOL"
    assert Token.TON.value == "TON"


def test_official_default_supported_assets_snapshot() -> None:
    expected = {
        Network.TRON.value: [Token.TRX.value, Token.USDT.value],
        Network.ETHEREUM.value: [Token.USDT.value, Token.USDC.value],
        Network.SOLANA.value: [Token.USDT.value, Token.USDC.value, Token.SOL.value],
        Network.BSC.value: [Token.USDT.value, Token.USDC.value],
        Network.POLYGON.value: [Token.USDT.value, Token.USDC.value, Token.USDC_E.value],
        Network.PLASMA.value: [Token.USDT.value],
        Network.TON.value: [Token.TON.value, Token.USDT.value],
        Network.APTOS.value: [Token.USDC.value, Token.USDT.value],
    }
    assert "binance" in expected
    assert expected[Network.TRON.value] == ["TRX", "USDT"]
    assert expected[Network.POLYGON.value] == ["USDT", "USDC", "USDC.e"]
    assert expected[Network.TON.value] == ["TON", "USDT"]
    assert expected[Network.APTOS.value] == ["USDC", "USDT"]


def test_public_config_from_dict_full_and_defaults() -> None:
    config = PublicConfig.from_dict(
        {
            "supported_assets": [
                {"network": "tron", "display_name": "TRON", "tokens": ["TRX", "USDT"]}
            ],
            "site": {"cashier_name": "Acme"},
            "epay": {"default_currency": "cny", "default_token": "USDT", "default_network": "tron"},
            "okpay": {"enabled": True, "allow_tokens": ["USDT"]},
            "version": "v1.0.8",
        }
    )
    assert isinstance(config, PublicConfig)
    assert config.supported_assets[0].tokens == ["TRX", "USDT"]
    assert config.site.cashier_name == "Acme"
    assert config.epay.default_token == "USDT"
    assert config.okpay.enabled is True
    assert config.version == "v1.0.8"

    empty = PublicConfig.from_dict({})
    assert empty.supported_assets == []
    assert isinstance(empty.site, SiteConfig)
    assert isinstance(empty.epay, EpayDefaults)
    assert isinstance(empty.okpay, OkpayConfig)
    assert empty.version == ""


def test_supported_asset_from_dict_coerces_types() -> None:
    asset = SupportedAsset.from_dict(
        {"network": "ton", "display_name": "TON", "tokens": ["TON", "USDT"]}
    )
    assert asset.network == "ton"
    assert asset.tokens == ["TON", "USDT"]


def test_create_order_response_requires_core_fields() -> None:
    with pytest.raises(KeyError):
        CreateOrderResponse.from_dict({"order_id": "ORD"})


def test_create_order_response_optional_fields_default() -> None:
    order = CreateOrderResponse.from_dict(
        {
            "trade_id": "T1",
            "order_id": "O1",
            "amount": 100,
            "currency": "CNY",
            "actual_amount": 14.29,
            "status": 1,
            "expiration_time": 1779530812,
        }
    )
    assert order.receive_address == ""
    assert order.token == ""
    assert order.payment_url == ""


def test_checkstatus_and_manual_payment_models() -> None:
    status = CheckStatusResponse.from_dict({"trade_id": "T1", "status": 2})
    assert status.status is OrderStatus.PAID

    manual = ManualPaymentResponse.from_dict(
        {"trade_id": "T1", "status": 2, "block_transaction_id": "0xabc"}
    )
    assert manual.block_transaction_id == "0xabc"


def test_gmpay_callback_from_dict_ignores_unknown_fields() -> None:
    callback = GmpayCallback.from_dict(
        {
            "pid": "1000",
            "trade_id": "T1",
            "order_id": "O1",
            "amount": 100,
            "actual_amount": 14.29,
            "receive_address": "addr",
            "token": "USDT",
            "block_transaction_id": "0xabc",
            "status": 2,
            "signature": "sig",
            "future_field": "ignored",
        }
    )
    assert callback.status is OrderStatus.PAID
    assert callback.signature == "sig"


def test_epay_callback_pid_is_int_and_trade_status_enum() -> None:
    callback = EpayCallback.from_dict(
        {
            "pid": "1000",
            "trade_no": "T1",
            "out_trade_no": "O1",
            "type": "alipay",
            "name": "VIP",
            "money": "100.0000",
            "trade_status": "TRADE_SUCCESS",
            "sign": "sig",
            "sign_type": "MD5",
        }
    )
    assert callback.pid == 1000
    assert callback.trade_status is TradeStatus.TRADE_SUCCESS


def test_qrcode_payload_prefers_receive_address() -> None:
    order = CreateOrderResponse(
        trade_id="T1",
        order_id="O1",
        amount=100,
        currency="CNY",
        actual_amount=14.29,
        receive_address="TAddress",
        token="USDT",
        status=OrderStatus.WAITING_PAYMENT,
        expiration_time=1779530812,
        payment_url="https://pay.example.com/checkout",
    )
    assert order._qrcode_payload() == "TAddress"

    order.receive_address = ""
    assert order._qrcode_payload() == "https://pay.example.com/checkout"

    order.payment_url = ""
    with pytest.raises(ValueError):
        order._qrcode_payload()


def test_generate_qrcode_smoke() -> None:
    pytest.importorskip("qrcode")
    order = CreateOrderResponse(
        trade_id="T1",
        order_id="O1",
        amount=100,
        currency="CNY",
        actual_amount=14.29,
        receive_address="TAddress",
        token="USDT",
        status=OrderStatus.WAITING_PAYMENT,
        expiration_time=1779530812,
        payment_url="",
    )
    data_uri = order.get_qrcode_data_uri()
    assert data_uri.startswith("data:image/png;base64,")
