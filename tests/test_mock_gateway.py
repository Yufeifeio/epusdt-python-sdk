from __future__ import annotations

import asyncio
from typing import Any, List

import pytest

from epusdt import (
    AsyncEpusdtClient,
    AuthenticationError,
    ClientError,
    EpusdtClient,
    NetworkError,
    RequestTimeoutError,
    ServerError,
    generate_epay_signature,
    generate_gmpay_signature,
)
from epusdt.exceptions import APIError
import requests
import httpx


class DummyResponse:
    def __init__(self, status_code: int, *, json_data: Any = None, text: str = "", headers=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class DummySession:
    def __init__(self, responses: List[Any]):
        self.responses = responses
        self.calls: List[dict] = []
        self.headers: dict = {}

    def request(self, method: str, url: str, timeout: float, **kwargs: Any):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def close(self) -> None:
        pass


class DummyAsyncSession:
    def __init__(self, responses: List[Any]):
        self.responses = responses
        self.calls: List[dict] = []
        self.headers: dict = {}

    async def request(self, method: str, url: str, timeout: float, **kwargs: Any):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def aclose(self) -> None:
        pass


def sync_client(responses: List[Any], **kw: Any) -> EpusdtClient:
    return EpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
        session=DummySession(responses),
        **kw,
    )


def async_client(responses: List[Any], **kw: Any) -> AsyncEpusdtClient:
    return AsyncEpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
        session=DummyAsyncSession(responses),
        **kw,
    )


def ok(data: Any) -> DummyResponse:
    return DummyResponse(200, json_data={"status_code": 200, "message": "success", "data": data, "request_id": "r"})


def test_create_order_json_shape_and_signature() -> None:
    client = sync_client([ok({
        "trade_id": "T", "order_id": "O", "amount": 100, "currency": "CNY",
        "actual_amount": 14.29, "receive_address": "a", "token": "USDT",
        "status": 1, "expiration_time": 1779530812, "payment_url": "u",
    })])
    client.create_order(
        order_id="O", amount=100, currency="cny", token="USDT", network="tron",
        notify_url="https://m.example/n",
    )
    call = client.session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/payments/gmpay/v1/order/create-transaction")
    body = call["kwargs"]["json"]
    assert body["pid"] == "1000"
    assert body["amount"] == 100
    expected_sig = generate_gmpay_signature(
        {k: v for k, v in body.items() if k != "signature"}, "epusdt_secret_key"
    )
    assert body["signature"] == expected_sig


def test_bsc_network_sends_binance() -> None:
    from epusdt import Network

    client = sync_client([ok({
        "trade_id": "T", "order_id": "O", "amount": 100, "currency": "CNY",
        "actual_amount": 14.29, "receive_address": "a", "token": "USDT",
        "status": 1, "expiration_time": 1779530812, "payment_url": "u",
    })])
    client.create_order(
        order_id="O", amount=100, currency="cny", token="USDT", network=Network.BSC,
        notify_url="https://m.example/n",
    )
    assert client.session.calls[0]["kwargs"]["json"]["network"] == "binance"


def test_get_config_check_status_switch_submit_paths() -> None:
    client = sync_client([
        ok({"supported_assets": [], "site": {}, "epay": {}, "okpay": {}, "version": "v"}),
        ok({"trade_id": "T", "status": 2}),
        ok({
            "trade_id": "T", "amount": 100, "actual_amount": 14.29, "token": "USDT",
            "currency": "CNY", "receive_address": "a", "network": "solana", "status": 1,
            "payment_type": "gmpay", "expiration_time": 1779530812000,
            "redirect_url": "", "payment_url": "", "created_at": 1779530212000,
            "is_selected": True,
        }),
        ok({"trade_id": "T", "status": 2, "block_transaction_id": "0xabc"}),
    ])
    client.get_public_config()
    client.check_status("T")
    client.switch_network(trade_id="T", token="USDT", network="solana")
    client.submit_tx_hash(trade_id="T", block_transaction_id="0xabc")
    methods = [(c["method"], c["url"]) for c in client.session.calls]
    assert methods[0] == ("GET", "https://pay.example.com/payments/gmpay/v1/config")
    assert methods[1] == ("GET", "https://pay.example.com/pay/check-status/T")
    assert methods[2] == ("POST", "https://pay.example.com/pay/switch-network")
    assert methods[3] == ("POST", "https://pay.example.com/pay/submit-tx-hash/T")
    assert client.session.calls[2]["kwargs"]["json"] == {
        "trade_id": "T", "token": "USDT", "network": "solana"
    }
    assert client.session.calls[3]["kwargs"]["json"] == {"block_transaction_id": "0xabc"}


def test_build_epay_redirect_url_has_signed_query() -> None:
    client = sync_client([])
    url = client.build_epay_redirect_url(
        out_trade_no="O", money=100, notify_url="https://m.example/n",
    )
    assert url.startswith(
        "https://pay.example.com/payments/epay/v1/order/create-transaction/submit.php?"
    )
    assert "sign=" in url and "sign_type=MD5" in url and "pid=1000" in url


def test_epay_get_uses_query_post_uses_form() -> None:
    client = sync_client([
        DummyResponse(302, headers={"Location": "/pay/checkout-counter/T"}),
        DummyResponse(302, headers={"Location": "/pay/checkout-counter/T"}),
    ])
    client.create_epay_order(out_trade_no="O", money=100, notify_url="https://m.example/n", method="GET")
    client.create_epay_order(out_trade_no="O", money=100, notify_url="https://m.example/n", method="POST")
    assert "params" in client.session.calls[0]["kwargs"]
    assert "data" in client.session.calls[1]["kwargs"]


def test_http_200_business_non_200_raises_apierror() -> None:
    client = sync_client([DummyResponse(200, json_data={"status_code": 10009, "message": "bad", "data": None})])
    with pytest.raises(APIError) as e:
        client.get_public_config()
    assert e.value.business_code == 10009


def test_http_401_raises_authentication_error() -> None:
    client = sync_client([DummyResponse(401, json_data={"status_code": 401, "message": "sig"}, text="sig")])
    with pytest.raises(AuthenticationError):
        client.get_public_config()


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_http_5xx_raises_server_error_no_retry_on_get_exhausted(code: int) -> None:
    client = sync_client([DummyResponse(code, text="err")] * 3, max_retries=2, retry_delay=0)
    with pytest.raises(ServerError) as e:
        client.get_public_config()
    assert e.value.http_status == code
    assert len(client.session.calls) == 3


def test_http_200_non_json_raises_client_error() -> None:
    client = sync_client([DummyResponse(200, text="<html>not json</html>")])
    with pytest.raises(ClientError):
        client.get_public_config()


def test_http_200_json_not_object_raises_client_error() -> None:
    client = sync_client([DummyResponse(200, json_data=[1, 2, 3])])
    with pytest.raises(ClientError):
        client.get_public_config()


def test_http_200_missing_data_raises_client_error() -> None:
    client = sync_client([DummyResponse(200, json_data={"status_code": 200, "message": "ok"})])
    with pytest.raises(ClientError):
        client.get_public_config()


def test_timeout_maps_to_request_timeout_error() -> None:
    client = sync_client([requests.Timeout("timed out")] * 3, max_retries=2, retry_delay=0)
    with pytest.raises(RequestTimeoutError):
        client.get_public_config()


def test_network_error_maps_to_network_error() -> None:
    client = sync_client([requests.ConnectionError("dns fail")] * 3, max_retries=2, retry_delay=0)
    with pytest.raises(NetworkError):
        client.get_public_config()


def test_create_order_does_not_retry_on_timeout() -> None:
    client = sync_client([requests.Timeout("t")] * 3, max_retries=2, retry_delay=0)
    with pytest.raises(RequestTimeoutError):
        client.create_order(order_id="O", amount=100, notify_url="https://m.example/n")
    assert len(client.session.calls) == 1


def test_get_retries_on_timeout_then_succeeds() -> None:
    client = sync_client(
        [requests.Timeout("t"), ok({"trade_id": "T", "status": 2})],
        max_retries=2,
        retry_delay=0,
    )
    result = client.check_status("T")
    assert result.trade_id == "T"
    assert len(client.session.calls) == 2


def test_secret_key_not_in_exception_text() -> None:
    client = sync_client([DummyResponse(401, json_data={"status_code": 401, "message": "sig err"}, text="sig err")])
    try:
        client.get_public_config()
    except AuthenticationError as exc:
        assert "epusdt_secret_key" not in str(exc)
        assert "epusdt_secret_key" not in (exc.response_text or "")


def test_async_matches_sync_paths_and_no_retry_on_write() -> None:
    async def run() -> None:
        client = async_client([httpx.TimeoutException("t")] * 3, max_retries=2, retry_delay=0)
        with pytest.raises(RequestTimeoutError):
            await client.create_order(order_id="O", amount=100, notify_url="https://m.example/n")
        assert len(client.session.calls) == 1

        client2 = async_client([
            httpx.TimeoutException("t"),
            ok({"trade_id": "T", "status": 2}),
        ], max_retries=2, retry_delay=0)
        res = await client2.check_status("T")
        assert res.trade_id == "T"
        assert len(client2.session.calls) == 2

    asyncio.run(run())


def test_async_epay_signature_consistent_with_sync() -> None:
    s = EpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="k")
    a = AsyncEpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="k")
    sp = s.build_epay_params(out_trade_no="O", money=88.5, notify_url="https://m.example/n")
    ap = a.build_epay_params(out_trade_no="O", money=88.5, notify_url="https://m.example/n")
    assert sp == ap
    assert sp["sign"] == generate_epay_signature(
        {k: v for k, v in sp.items() if k not in ("sign", "sign_type")}, "k"
    )


def test_async_all_endpoints_paths_and_shapes() -> None:
    async def run() -> None:
        client = async_client([
            ok({
                "trade_id": "T", "order_id": "O", "amount": 100, "currency": "CNY",
                "actual_amount": 14.29, "receive_address": "a", "token": "USDT",
                "status": 1, "expiration_time": 1779530812, "payment_url": "u",
            }),
            ok({"supported_assets": [], "site": {}, "epay": {}, "okpay": {}, "version": "v"}),
            ok({
                "trade_id": "T", "amount": 100, "actual_amount": 14.29, "token": "USDT",
                "currency": "CNY", "receive_address": "a", "network": "tron", "status": 1,
                "payment_type": "gmpay", "expiration_time": 1779530812000,
                "redirect_url": "", "payment_url": "", "created_at": 1779530212000,
                "is_selected": False,
            }),
            ok({"trade_id": "T", "status": 2}),
            ok({
                "trade_id": "T", "amount": 100, "actual_amount": 14.29, "token": "USDT",
                "currency": "CNY", "receive_address": "a", "network": "solana", "status": 1,
                "payment_type": "gmpay", "expiration_time": 1779530812000,
                "redirect_url": "", "payment_url": "", "created_at": 1779530212000,
                "is_selected": True,
            }),
            ok({"trade_id": "T", "status": 2, "block_transaction_id": "0xabc"}),
        ])
        await client.create_order(order_id="O", amount=100, token="USDT", network="tron", notify_url="https://m.example/n")
        await client.get_public_config()
        await client.get_checkout("T")
        await client.check_status("T")
        await client.switch_network(trade_id="T", token="USDT", network="solana")
        await client.submit_tx_hash(trade_id="T", block_transaction_id="0xabc")
        urls = [(c["method"], c["url"]) for c in client.session.calls]
        assert urls == [
            ("POST", "https://pay.example.com/payments/gmpay/v1/order/create-transaction"),
            ("GET", "https://pay.example.com/payments/gmpay/v1/config"),
            ("GET", "https://pay.example.com/pay/checkout-counter-resp/T"),
            ("GET", "https://pay.example.com/pay/check-status/T"),
            ("POST", "https://pay.example.com/pay/switch-network"),
            ("POST", "https://pay.example.com/pay/submit-tx-hash/T"),
        ]

    asyncio.run(run())


def test_async_http_matrix() -> None:
    async def run() -> None:
        c1 = async_client([DummyResponse(200, json_data={"status_code": 10008, "message": "x", "data": None})])
        with pytest.raises(APIError):
            await c1.get_public_config()
        c2 = async_client([DummyResponse(401, json_data={"status_code": 401, "message": "sig"}, text="sig")])
        with pytest.raises(AuthenticationError):
            await c2.get_public_config()
        c3 = async_client([DummyResponse(500, text="e")] * 3, max_retries=2, retry_delay=0)
        with pytest.raises(ServerError):
            await c3.get_public_config()
        c4 = async_client([DummyResponse(200, text="<html>")])
        with pytest.raises(ClientError):
            await c4.get_public_config()
        c5 = async_client([DummyResponse(200, json_data=[1])])
        with pytest.raises(ClientError):
            await c5.get_public_config()
        c6 = async_client([DummyResponse(200, json_data={"status_code": 200, "message": "ok"})])
        with pytest.raises(ClientError):
            await c6.get_public_config()

    asyncio.run(run())


def test_async_epay_redirect_and_html_error() -> None:
    async def run() -> None:
        a = AsyncEpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="k")
        url = a.build_epay_redirect_url(out_trade_no="O", money=100, notify_url="https://m.example/n")
        assert "submit.php?" in url and "sign=" in url

        c = async_client([DummyResponse(200, text="<html>error</html>")])
        with pytest.raises(ClientError):
            await c.create_epay_order(out_trade_no="O", money=100, notify_url="https://m.example/n")

    asyncio.run(run())


def test_async_context_manager_closes_owned_session_only() -> None:
    async def run() -> None:
        closed = {"v": False}
        class S(DummyAsyncSession):
            async def aclose(self) -> None:
                closed["v"] = True

        external = S([])
        async with AsyncEpusdtClient(
            base_url="https://pay.example.com", pid="1000", secret_key="k", session=external
        ):
            pass
        assert closed["v"] is False

    asyncio.run(run())



def test_async_build_epay_params_all_optional_fields_and_network_error() -> None:
    async def run() -> None:
        a = AsyncEpusdtClient(base_url="https://pay.example.com", pid="1000", secret_key="k")
        params = a.build_epay_params(
            out_trade_no="O",
            money=88.5,
            notify_url="https://m.example/n",
            return_url="https://m.example/r",
            name="VIP",
            token="USDT",
            network="tron",
            currency="cny",
        )
        for key in ("return_url", "name", "token", "network", "currency", "sign", "sign_type"):
            assert key in params

        c = async_client([httpx.ConnectError("dns")] * 3, max_retries=2, retry_delay=0)
        with pytest.raises(NetworkError):
            await c.get_public_config()

        await a.close()

    asyncio.run(run())
