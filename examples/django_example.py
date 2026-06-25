import json
import os
import time
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from epusdt import EpusdtClient, OrderStatus, SignatureError, TradeStatus


client = EpusdtClient(
    base_url=os.environ["EPUSDT_BASE_URL"],
    pid=os.environ["EPUSDT_PID"],
    secret_key=os.environ["EPUSDT_SECRET_KEY"],
)


def mark_order_paid(*, order_id: str, trade_id: str, payload: Any) -> None:
    _ = (order_id, trade_id, payload)


@require_POST
def create_order(request: HttpRequest) -> JsonResponse:
    order = client.create_order(
        order_id=f"DJANGO_{int(time.time())}",
        amount=100,
        currency="cny",
        token="USDT",
        network="tron",
        notify_url="https://merchant.example.com/notify/gmpay",
        redirect_url="https://merchant.example.com/return",
        name="会员充值",
    )
    return JsonResponse(
        {
            "trade_id": order.trade_id,
            "payment_url": order.payment_url,
            "actual_amount": order.actual_amount,
        }
    )


@csrf_exempt
@require_POST
def gmpay_notify(request: HttpRequest) -> HttpResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponse("fail", status=400)

    try:
        callback = client.parse_gmpay_callback(payload)
    except SignatureError:
        return HttpResponse("fail", status=400)

    if callback.status == OrderStatus.PAID:
        mark_order_paid(
            order_id=callback.order_id,
            trade_id=callback.trade_id,
            payload=payload,
        )

    return HttpResponse("ok", status=200)


@csrf_exempt
@require_GET
def epay_notify(request: HttpRequest) -> HttpResponse:
    params = request.GET.dict()
    try:
        callback = client.parse_epay_callback(params)
    except SignatureError:
        return HttpResponse("fail", status=400)

    if callback.trade_status == TradeStatus.TRADE_SUCCESS:
        mark_order_paid(
            order_id=callback.out_trade_no,
            trade_id=callback.trade_no,
            payload=params,
        )

    return HttpResponse("success", status=200)
