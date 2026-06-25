from __future__ import annotations

from decimal import Decimal

import pytest

from epusdt import (
    build_epay_signing_string,
    build_gmpay_signing_string,
    generate_epay_signature,
    generate_gmpay_signature,
    verify_epay_signature,
    verify_gmpay_signature,
)
from epusdt.signature import _build_signing_string, stringify_params
from epusdt.exceptions import ValidationError


def test_gmpay_signature_matches_docs() -> None:
    params = {
        "pid": "1000",
        "order_id": "ORD202605230001",
        "currency": "cny",
        "token": "usdt",
        "network": "tron",
        "amount": 100,
        "notify_url": "https://merchant.example/notify",
        "redirect_url": "https://merchant.example/return",
        "name": "VIP",
    }
    signing = build_gmpay_signing_string(params)
    assert signing == (
        "amount=100&currency=cny&name=VIP&network=tron&"
        "notify_url=https://merchant.example/notify&"
        "order_id=ORD202605230001&pid=1000&"
        "redirect_url=https://merchant.example/return&token=usdt"
    )
    # 官方 GMWalletApp/epusdt src/util/sign/sign.go 算法计算出的真实向量。
    assert generate_gmpay_signature(params, "epusdt_secret_key") == "476412c422f4dd75c3d533f5c47a9cac"


def test_epay_signature_matches_docs() -> None:
    params = {
        "pid": "1000",
        "money": 100,
        "out_trade_no": "ORD202605230001",
        "notify_url": "https://merchant.example/notify",
        "return_url": "https://merchant.example/return",
        "name": "VIP",
        "type": "alipay",
    }
    signing = build_epay_signing_string(params)
    assert signing == (
        "money=100&name=VIP&notify_url=https://merchant.example/notify&"
        "out_trade_no=ORD202605230001&pid=1000&"
        "return_url=https://merchant.example/return&type=alipay"
    )
    assert generate_epay_signature(params, "epusdt_secret_key") == "b865b0acbb2b01554c35a1bd33351452"


def test_signature_verification_helpers() -> None:
    gmpay = {"pid": "1000", "order_id": "A001", "amount": 1, "signature": ""}
    gmpay["signature"] = generate_gmpay_signature(gmpay, "secret")
    assert verify_gmpay_signature(gmpay, "secret")

    epay = {"pid": "1000", "money": 1, "out_trade_no": "A001", "sign_type": "MD5", "sign": ""}
    epay["sign"] = generate_epay_signature(epay, "secret")
    assert verify_epay_signature(epay, "secret")


def test_excludes_signature_and_sign_fields() -> None:
    # signature 不参与 GMPay 签名串。
    assert "signature=" not in build_gmpay_signing_string({"a": "1", "signature": "x"})
    # sign / sign_type 不参与 EPay 签名串。
    s = build_epay_signing_string({"a": "1", "sign": "x", "sign_type": "MD5"})
    assert "sign=" not in s
    assert "sign_type=" not in s


def test_none_and_empty_string_excluded() -> None:
    s = build_gmpay_signing_string({"a": "1", "b": None, "c": "", "d": "2"})
    assert s == "a=1&d=2"


def test_numeric_types_are_signature_equivalent() -> None:
    # 100 / 100.0 / "100" / Decimal("100") / Decimal("100.00") 必须签名一致。
    for value in (100, 100.0, "100", Decimal("100"), Decimal("100.00")):
        assert build_gmpay_signing_string({"amount": value}) == "amount=100"


def test_decimal_fraction_drops_trailing_zeros_like_go() -> None:
    # 官方 strconv.FormatFloat(f,'f',-1,64) 会去掉末尾 0：100.50 -> 100.5。
    assert build_gmpay_signing_string({"amount": Decimal("100.50")}) == "amount=100.5"
    assert build_gmpay_signing_string({"amount": 100.50}) == "amount=100.5"
    assert build_gmpay_signing_string({"amount": "100.00"}) == "amount=100.00"  # 字符串保留原样


def test_chinese_and_special_chars_signed_verbatim() -> None:
    s = build_gmpay_signing_string({"name": "会员充值", "note": "a&b=c d"})
    assert s == "name=会员充值&note=a&b=c d"


def test_token_level_sort_matches_go_for_prefix_collisions() -> None:
    # key "a" 与 "a-b"：按 key 排序得到 [a, a-b]，但官方按整体 token 排序
    # ("a-b=..." < "a=..." 因为 '-'(0x2D) < '='(0x3D))，必须与官方一致。
    s = _build_signing_string({"a": "1", "a-b": "2"}, excluded=())
    assert s == "a-b=2&a=1"


def test_bool_rejected() -> None:
    with pytest.raises(ValidationError):
        build_gmpay_signing_string({"flag": True})


def test_nan_and_infinity_rejected() -> None:
    with pytest.raises(ValidationError):
        build_gmpay_signing_string({"amount": float("nan")})
    with pytest.raises(ValidationError):
        build_gmpay_signing_string({"amount": float("inf")})
    with pytest.raises(ValidationError):
        build_gmpay_signing_string({"amount": Decimal("Infinity")})


def test_bytes_decoded_utf8() -> None:
    assert build_gmpay_signing_string({"x": b"abc"}) == "x=abc"


def test_verify_uses_constant_time_and_rejects_tampering() -> None:
    payload = {"pid": "1000", "order_id": "A1", "amount": 1}
    sig = generate_gmpay_signature(payload, "secret")
    good = dict(payload, signature=sig)
    bad = dict(payload, signature=sig[:-1] + ("0" if sig[-1] != "0" else "1"))
    assert verify_gmpay_signature(good, "secret") is True
    assert verify_gmpay_signature(bad, "secret") is False
    # 缺少签名直接判否。
    assert verify_gmpay_signature(payload, "secret") is False


def test_verify_with_explicit_signature_argument() -> None:
    payload = {"pid": "1000", "order_id": "A1", "amount": 1}
    sig = generate_gmpay_signature(payload, "secret")
    assert verify_gmpay_signature(payload, "secret", signature=sig) is True


def test_uppercase_signature_not_accepted() -> None:
    # 官方输出小写 hex，大写不应通过（验签是精确比较）。
    payload = {"pid": "1000", "order_id": "A1", "amount": 1}
    sig = generate_gmpay_signature(payload, "secret")
    assert verify_gmpay_signature(dict(payload, signature=sig.upper()), "secret") is False


def test_stringify_params_matches_signature_values() -> None:
    # form 模式发送的字符串必须与签名串使用的字符串一致。
    params = {"amount": 100.5, "n": Decimal("100.00"), "s": "x", "skip": None}
    out = stringify_params(params)
    assert out == {"amount": "100.5", "n": "100", "s": "x"}
