from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional
from urllib.parse import urlencode, urljoin

import httpx

from .client import (
    EPAY_SUBMIT_PATH,
    USER_AGENT,
    _coerce_int,
    _is_numeric_pid,
    _json_value,
    _normalize_amount,
    _normalize_base_url,
    _optional_text,
    _require_text,
    _validate_url,
)
from .exceptions import (
    AuthenticationError,
    ClientError,
    NetworkError,
    RequestTimeoutError,
    ServerError,
    SignatureError,
    ValidationError,
    create_api_error,
)
from .models import (
    CheckStatusResponse,
    CheckoutOrder,
    CreateOrderResponse,
    EPayRedirectResponse,
    EpayCallback,
    GmpayCallback,
    ManualPaymentResponse,
    PublicConfig,
)
from .retry import async_call_with_retry
from .signature import (
    generate_epay_signature,
    generate_gmpay_signature,
    stringify_params,
    verify_epay_signature,
    verify_gmpay_signature,
)
from .client import _response_request_id


class AsyncEpusdtClient:
    def __init__(
        self,
        *,
        base_url: str,
        pid: Any,
        secret_key: str,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        session: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if timeout <= 0:
            raise ValidationError("timeout must be greater than 0")
        if max_retries < 0:
            raise ValidationError("max_retries must be >= 0")
        if retry_delay < 0:
            raise ValidationError("retry_delay must be >= 0")

        self.base_url = _normalize_base_url(base_url)
        self.pid = _require_text("pid", pid)
        self.secret_key = _require_text("secret_key", secret_key)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._owns_session = session is None
        self.session = session or httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
        )
        self.session.headers.setdefault("Accept", "application/json")
        self.session.headers.setdefault("User-Agent", USER_AGENT)

    async def aclose(self) -> None:
        if self._owns_session and hasattr(self.session, "aclose"):
            await self.session.aclose()

    async def __aenter__(self) -> "AsyncEpusdtClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()

    async def create_order(
        self,
        *,
        order_id: Any,
        amount: Any,
        currency: Any = "cny",
        notify_url: str,
        token: Optional[Any] = None,
        network: Optional[Any] = None,
        redirect_url: Optional[str] = None,
        name: Optional[Any] = None,
        payment_type: Optional[Any] = None,
        use_form: bool = False,
    ) -> CreateOrderResponse:
        token_text = _optional_text("token", token)
        network_text = _optional_text("network", network)
        if bool(token_text) != bool(network_text):
            raise ValidationError("token and network must be both provided or both omitted")

        payload: MutableMapping[str, Any] = {
            "pid": self.pid,
            "order_id": _require_text("order_id", order_id),
            "currency": _require_text("currency", currency),
            "amount": _normalize_amount("amount", amount),
            "notify_url": _validate_url("notify_url", _require_text("notify_url", notify_url)),
        }
        if token_text:
            payload["token"] = token_text
        if network_text:
            payload["network"] = network_text
        redirect = _optional_text("redirect_url", redirect_url)
        if redirect:
            payload["redirect_url"] = _validate_url("redirect_url", redirect)
        name_text = _optional_text("name", name)
        if name_text:
            payload["name"] = name_text
        payment_type_text = _optional_text("payment_type", payment_type)
        if payment_type_text:
            if payment_type_text.lower() == "epay" and not _is_numeric_pid(self.pid):
                raise ValidationError("payment_type=Epay requires a numeric pid")
            payload["payment_type"] = payment_type_text

        payload["signature"] = generate_gmpay_signature(payload, self.secret_key)
        body = await self._json_request(
            "POST",
            "/payments/gmpay/v1/order/create-transaction",
            json_payload=payload if not use_form else None,
            form_payload=payload if use_form else None,
        )
        return CreateOrderResponse.from_dict(body["data"])

    async def get_public_config(self) -> PublicConfig:
        body = await self._json_request("GET", "/payments/gmpay/v1/config")
        return PublicConfig.from_dict(body["data"])

    async def get_checkout(self, trade_id: Any) -> CheckoutOrder:
        body = await self._json_request(
            "GET",
            f"/pay/checkout-counter-resp/{_require_text('trade_id', trade_id)}",
        )
        return CheckoutOrder.from_dict(body["data"])

    async def check_status(self, trade_id: Any) -> CheckStatusResponse:
        body = await self._json_request(
            "GET",
            f"/pay/check-status/{_require_text('trade_id', trade_id)}",
        )
        return CheckStatusResponse.from_dict(body["data"])

    async def switch_network(self, *, trade_id: Any, token: Any, network: Any) -> CheckoutOrder:
        payload = {
            "trade_id": _require_text("trade_id", trade_id),
            "token": _require_text("token", token),
            "network": _require_text("network", network),
        }
        body = await self._json_request("POST", "/pay/switch-network", json_payload=payload)
        return CheckoutOrder.from_dict(body["data"])

    async def submit_tx_hash(
        self,
        *,
        trade_id: Any,
        block_transaction_id: Any,
    ) -> ManualPaymentResponse:
        payload = {
            "block_transaction_id": _require_text("block_transaction_id", block_transaction_id),
        }
        body = await self._json_request(
            "POST",
            f"/pay/submit-tx-hash/{_require_text('trade_id', trade_id)}",
            json_payload=payload,
        )
        return ManualPaymentResponse.from_dict(body["data"])

    def build_epay_params(
        self,
        *,
        out_trade_no: Any,
        money: Any,
        notify_url: str,
        return_url: Optional[str] = None,
        name: Optional[Any] = None,
        type: Any = "alipay",
        token: Optional[Any] = None,
        network: Optional[Any] = None,
        currency: Optional[Any] = None,
        sign_type: str = "MD5",
    ) -> dict[str, str]:
        if not _is_numeric_pid(self.pid):
            raise ValidationError("EPay compatibility mode requires a numeric pid")

        params: MutableMapping[str, Any] = {
            "pid": self.pid,
            "money": _normalize_amount("money", money),
            "out_trade_no": _require_text("out_trade_no", out_trade_no),
            "notify_url": _validate_url("notify_url", _require_text("notify_url", notify_url)),
            "type": _require_text("type", type),
        }
        if return_url:
            params["return_url"] = _validate_url("return_url", _require_text("return_url", return_url))
        name_text = _optional_text("name", name)
        if name_text:
            params["name"] = name_text
        token_text = _optional_text("token", token)
        if token_text:
            params["token"] = token_text
        network_text = _optional_text("network", network)
        if network_text:
            params["network"] = network_text
        currency_text = _optional_text("currency", currency)
        if currency_text:
            params["currency"] = currency_text
        params["sign_type"] = _require_text("sign_type", sign_type)
        params["sign"] = generate_epay_signature(params, self.secret_key)
        return dict(stringify_params(params))

    def build_epay_redirect_url(self, **kwargs: Any) -> str:
        params = self.build_epay_params(**kwargs)
        return f"{self.base_url}{EPAY_SUBMIT_PATH}?{urlencode(params)}"

    async def create_epay_order(
        self,
        *,
        method: str = "GET",
        **kwargs: Any,
    ) -> EPayRedirectResponse:
        params = self.build_epay_params(**kwargs)
        method_upper = method.upper()
        if method_upper not in {"GET", "POST"}:
            raise ValidationError("method must be GET or POST")

        if method_upper == "GET":
            response = await self._request(
                method_upper,
                EPAY_SUBMIT_PATH,
                params=params,
                follow_redirects=False,
            )
        else:
            response = await self._request(
                method_upper,
                EPAY_SUBMIT_PATH,
                data=params,
                follow_redirects=False,
            )

        if 300 <= response.status_code < 400 and response.headers.get("Location"):
            location = response.headers["Location"]
            return EPayRedirectResponse(
                status_code=response.status_code,
                location=location,
                checkout_url=urljoin(f"{self.base_url}/", location),
                params=params,
            )

        payload = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        self._raise_for_response(response, payload if isinstance(payload, Mapping) else None)
        raise ClientError(
            f"unexpected response status: {response.status_code}",
            http_status=response.status_code,
            response_text=response.text,
        )

    def verify_gmpay_callback(
        self,
        payload: Mapping[str, Any],
        *,
        secret_key: Optional[str] = None,
    ) -> bool:
        return verify_gmpay_signature(payload, secret_key or self.secret_key)

    def parse_gmpay_callback(
        self,
        payload: Mapping[str, Any],
        *,
        verify: bool = True,
        secret_key: Optional[str] = None,
    ) -> GmpayCallback:
        if verify and not self.verify_gmpay_callback(payload, secret_key=secret_key):
            raise SignatureError("invalid GMPay callback signature")
        return GmpayCallback.from_dict(payload)

    def verify_epay_callback(
        self,
        params: Mapping[str, Any],
        *,
        secret_key: Optional[str] = None,
    ) -> bool:
        return verify_epay_signature(params, secret_key or self.secret_key)

    def parse_epay_callback(
        self,
        params: Mapping[str, Any],
        *,
        verify: bool = True,
        secret_key: Optional[str] = None,
    ) -> EpayCallback:
        if verify and not self.verify_epay_callback(params, secret_key=secret_key):
            raise SignatureError("invalid EPay callback signature")
        return EpayCallback.from_dict(params)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"

        async def send() -> httpx.Response:
            try:
                response = await self.session.request(method, url, timeout=self.timeout, **kwargs)
            except httpx.TimeoutException as exc:
                raise RequestTimeoutError(str(exc)) from exc
            except httpx.RequestError as exc:
                raise NetworkError(str(exc)) from exc
            if response.status_code >= 500:
                raise ServerError(
                    f"gateway returned HTTP {response.status_code}",
                    http_status=response.status_code,
                    response_text=response.text,
                )
            return response

        return await async_call_with_retry(
            send,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            retry_name=f"{method} {path}",
        )

    async def _json_request(
        self,
        method: str,
        path: str,
        *,
        json_payload: Optional[Mapping[str, Any]] = None,
        form_payload: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        kwargs: dict[str, Any] = {}
        if json_payload is not None:
            kwargs["json"] = {key: _json_value(value) for key, value in json_payload.items()}
        if form_payload is not None:
            kwargs["data"] = stringify_params(form_payload)
        response = await self._request(method, path, **kwargs)
        return self._parse_json_response(response)

    def _parse_json_response(self, response: httpx.Response) -> Mapping[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            if response.status_code >= 400:
                self._raise_for_response(response)
            raise ClientError(
                "gateway did not return valid JSON",
                http_status=response.status_code,
                response_text=response.text,
            ) from exc

        if not isinstance(payload, dict):
            raise ClientError(
                "gateway JSON response must be an object",
                http_status=response.status_code,
                response_text=json.dumps(payload, ensure_ascii=False),
            )

        if response.status_code >= 400:
            self._raise_for_response(response, payload)

        business_code = _coerce_int(payload.get("status_code"))
        if business_code != 200:
            raise create_api_error(
                str(payload.get("message", "epusdt API error")),
                business_code=business_code,
                http_status=response.status_code,
                response=payload,
                request_id=_response_request_id(payload),
            )
        return payload

    def _raise_for_response(
        self,
        response: httpx.Response,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> None:
        message = ""
        business_code = None
        if isinstance(payload, Mapping):
            message = str(payload.get("message", "")).strip()
            business_code = _coerce_int(payload.get("status_code"))
        if not message:
            message = response.text.strip() or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(
                message,
                http_status=response.status_code,
                response_text=response.text,
            )
        if payload is not None:
            raise create_api_error(
                message,
                business_code=business_code,
                http_status=response.status_code,
                response=payload,
                request_id=_response_request_id(payload),
            )
        raise ClientError(
            message,
            http_status=response.status_code,
            response_text=response.text,
        )
