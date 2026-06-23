from __future__ import annotations

import asyncio
from typing import Any

from epusdt import (
    APIError,
    AsyncEpusdtClient,
    OrderStatus,
    PaymentType,
    SignatureError,
    generate_epay_signature,
    generate_gmpay_signature,
)


class DummyAsyncResponse:
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


class DummyAsyncSession:
    def __init__(self, responses: list[DummyAsyncResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []
        self.headers: dict[str, str] = {}
        self.closed = False

    async def request(self, method: str, url: str, timeout: float, **kwargs: Any) -> DummyAsyncResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        return self.responses.pop(0)

    async def aclose(self) -> None:
        self.closed = True


def test_async_create_order_and_context_manager() -> None:
    async def run() -> None:
        session = DummyAsyncSession(
            [
                DummyAsyncResponse(
                    200,
                    json_data={
                        "status_code": "200",
                        "message": "success",
                        "data": {
                            "trade_id": "ATRADE001",
                            "order_id": "AORD001",
                            "amount": "100.50",
                            "currency": "CNY",
                            "actual_amount": "14.29",
                            "receive_address": "TTestTronAddress001",
                            "token": "USDT",
                            "status": 1,
                            "expiration_time": 1779530812,
                            "payment_url": "https://pay.example.com/pay/checkout-counter/ATRADE001",
                        },
                        "request_id": "arid-1",
                    },
                )
            ]
        )
        async with AsyncEpusdtClient(
            base_url="https://pay.example.com/payments/epay/v1/order/create-transaction/submit.php",
            pid="1000",
            secret_key="secret",
            session=session,
        ) as client:
            order = await client.create_order(
                order_id="AORD001",
                amount="100.50",
                currency="cny",
                notify_url="https://merchant.example/notify",
            )
            assert client.base_url == "https://pay.example.com"
            assert session.calls[0]["kwargs"]["json"]["amount"] == 100.5
            assert order.status is OrderStatus.WAITING_PAYMENT
        assert session.closed is False

    asyncio.run(run())


def test_async_create_epay_order_returns_redirect() -> None:
    async def run() -> None:
        session = DummyAsyncSession(
            [
                DummyAsyncResponse(
                    302,
                    text="",
                    headers={"Location": "/pay/checkout-counter/ATRADE002"},
                )
            ]
        )
        client = AsyncEpusdtClient(
            base_url="https://pay.example.com",
            pid="1000",
            secret_key="epusdt_secret_key",
            session=session,
        )
        redirect = await client.create_epay_order(
            out_trade_no="AORD002",
            money=100,
            notify_url="https://merchant.example/notify",
            return_url="https://merchant.example/return",
            name="VIP",
        )
        assert redirect.status_code == 302
        assert redirect.location == "/pay/checkout-counter/ATRADE002"
        assert redirect.checkout_url == "https://pay.example.com/pay/checkout-counter/ATRADE002"

    asyncio.run(run())


def test_async_callback_helpers() -> None:
    client = AsyncEpusdtClient(
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

    bad_payload = dict(gmpay_payload)
    bad_payload["signature"] = "bad"
    try:
        client.parse_gmpay_callback(bad_payload)
    except SignatureError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected SignatureError")


def test_async_get_checkout_parses_payment_type() -> None:
    async def run() -> None:
        session = DummyAsyncSession(
            [
                DummyAsyncResponse(
                    200,
                    json_data={
                        "status_code": 200,
                        "message": "success",
                        "data": {
                            "trade_id": "ATRADE003",
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
                        "request_id": "arid-3",
                    },
                )
            ]
        )
        client = AsyncEpusdtClient(
            base_url="https://pay.example.com",
            pid="1000",
            secret_key="secret",
            session=session,
        )
        checkout = await client.get_checkout("ATRADE003")
        assert checkout.payment_type is PaymentType.GMPAY

    asyncio.run(run())


def test_async_create_epay_order_raises_api_error_on_json_failure() -> None:
    async def run() -> None:
        session = DummyAsyncSession(
            [
                DummyAsyncResponse(
                    400,
                    json_data={
                        "status_code": 10009,
                        "message": "params error",
                        "data": None,
                        "request_id": "arid-4",
                    },
                    text='{"status_code":10009,"message":"params error"}',
                )
            ]
        )
        client = AsyncEpusdtClient(
            base_url="https://pay.example.com",
            pid="1000",
            secret_key="secret",
            session=session,
        )
        try:
            await client.create_epay_order(
                out_trade_no="AORD004",
                money=100,
                notify_url="https://merchant.example/notify",
            )
        except APIError as exc:
            assert exc.business_code == 10009
        else:  # pragma: no cover
            raise AssertionError("expected APIError")

    asyncio.run(run())
