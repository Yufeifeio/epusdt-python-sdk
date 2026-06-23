from time import time

from fastapi import FastAPI, HTTPException, Request

from epusdt import EpusdtClient, OrderStatus, SignatureError, TradeStatus


app = FastAPI()

client = EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
)


@app.post("/create-order")
async def create_order():
    order = client.create_order(
        order_id=f"FASTAPI_{int(time())}",
        amount=100,
        currency="cny",
        token="USDT",
        network="tron",
        notify_url="https://merchant.example.com/notify",
        redirect_url="https://merchant.example.com/return",
        name="会员充值",
    )
    return {
        "trade_id": order.trade_id,
        "payment_url": order.payment_url,
        "actual_amount": order.actual_amount,
    }


@app.post("/notify/gmpay")
async def gmpay_notify(request: Request):
    payload = await request.json()
    try:
        callback = client.parse_gmpay_callback(payload)
    except SignatureError as exc:
        raise HTTPException(status_code=400, detail="签名错误") from exc

    if callback.status == OrderStatus.PAID:
        # 在这里写你自己的订单处理逻辑
        pass

    return "ok"


@app.get("/notify/epay")
async def epay_notify(request: Request):
    params = dict(request.query_params)
    try:
        callback = client.parse_epay_callback(params)
    except SignatureError as exc:
        raise HTTPException(status_code=400, detail="签名错误") from exc

    if callback.trade_status == TradeStatus.TRADE_SUCCESS:
        # 在这里写你自己的订单处理逻辑
        pass

    return "success"
