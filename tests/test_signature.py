from epusdt import (
    build_epay_signing_string,
    build_gmpay_signing_string,
    generate_epay_signature,
    generate_gmpay_signature,
    verify_epay_signature,
    verify_gmpay_signature,
)


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

