"""本地参数校验与金额边界（Section 六）专项测试。"""
from __future__ import annotations

from decimal import Decimal

import pytest

from epusdt import EpusdtClient, ValidationError, Network, Token


def client(**kw):
    return EpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="k", **kw)


def test_constructor_validates_timeout_retries():
    with pytest.raises(ValidationError):
        client(timeout=0)
    with pytest.raises(ValidationError):
        client(max_retries=-1)
    with pytest.raises(ValidationError):
        client(retry_delay=-1)


def test_constructor_requires_pid_and_secret():
    with pytest.raises(ValidationError):
        EpusdtClient(base_url="https://pay.example.com", pid="", secret_key="k")
    with pytest.raises(ValidationError):
        EpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="")


def test_base_url_must_be_http():
    with pytest.raises(ValidationError):
        EpusdtClient(base_url="ftp://x", pid="1000", secret_key="k")
    with pytest.raises(ValidationError):
        EpusdtClient(base_url="not-a-url", pid="1000", secret_key="k")


@pytest.mark.parametrize("bad", [0, 0.01, Decimal("0.01"), "0.01", -1, "0"])
def test_amount_at_or_below_min_rejected(bad):
    c = client()
    with pytest.raises(ValidationError):
        c.create_order(order_id="O", amount=bad, notify_url="https://m.example/n")


@pytest.mark.parametrize("good", [0.02, 1, 1.00, 88.5, 100, Decimal("100.00"), "100.50"])
def test_amount_above_min_accepted_by_normalizer(good):
    from epusdt.client import _normalize_amount

    # 不应抛异常
    _normalize_amount("amount", good)


def test_amount_rejects_non_number_and_bool():
    from epusdt.client import _normalize_amount

    with pytest.raises(ValidationError):
        _normalize_amount("amount", True)
    with pytest.raises(ValidationError):
        _normalize_amount("amount", "abc")
    with pytest.raises(ValidationError):
        _normalize_amount("amount", object())


def test_integral_amount_becomes_int_fraction_becomes_float():
    from epusdt.client import _normalize_amount

    assert _normalize_amount("a", Decimal("100.00")) == 100
    assert isinstance(_normalize_amount("a", Decimal("100.00")), int)
    assert _normalize_amount("a", Decimal("100.50")) == 100.5
    assert isinstance(_normalize_amount("a", "100.50"), float)


def test_notify_url_must_be_valid_http():
    c = client()
    with pytest.raises(ValidationError):
        c.create_order(order_id="O", amount=100, notify_url="javascript:alert(1)")
    with pytest.raises(ValidationError):
        c.create_order(order_id="O", amount=100, notify_url="ftp://x/y")


def test_token_network_must_be_both_or_neither():
    c = client()
    with pytest.raises(ValidationError):
        c.create_order(order_id="O", amount=100, notify_url="https://m.example/n", token="USDT")
    with pytest.raises(ValidationError):
        c.create_order(order_id="O", amount=100, notify_url="https://m.example/n", network="tron")


def test_epay_redirect_url_rejects_non_numeric_pid():
    c = EpusdtClient(base_url="https://pay.example.com", pid="merchant-a", secret_key="k")
    with pytest.raises(ValidationError):
        c.build_epay_redirect_url(out_trade_no="O", money=100, notify_url="https://m.example/n")


def test_create_epay_order_rejects_bad_method():
    c = client()
    with pytest.raises(ValidationError):
        c.create_epay_order(out_trade_no="O", money=100, notify_url="https://m.example/n", method="PUT")


def test_base_url_normalizes_trailing_slash_and_epay_suffix():
    c1 = EpusdtClient(base_url="https://pay.example.com/", pid="1000", secret_key="k")
    assert c1.base_url == "https://pay.example.com"
    c2 = EpusdtClient(
        base_url="https://pay.example.com/gw/payments/epay/v1/order/create-transaction/submit.php",
        pid="1000",
        secret_key="k",
    )
    assert c2.base_url == "https://pay.example.com/gw"


def test_enum_inputs_serialized_to_wire_values():
    from epusdt.client import _optional_text

    assert _optional_text("network", Network.BSC) == "binance"
    assert _optional_text("token", Token.USDT) == "USDT"
