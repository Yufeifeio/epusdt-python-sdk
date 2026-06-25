import os
from time import time

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from epusdt import AsyncEpusdtClient, OrderStatus, SignatureError, TradeStatus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 不要在源码里硬编码真实密钥，统一从环境变量读取。
    app.state.epusdt = AsyncEpusdtClient(
        base_url=os.environ["EPUSDT_BASE_URL"],
        pid=os.environ["EPUSDT_PID"],
        secret_key=os.environ["EPUSDT_SECRET_KEY"],
    )
    try:
        yield
    finally:
        await app.state.epusdt.aclose()


app = FastAPI(lifespan=lifespan)


def get_client(request: Request) -> AsyncEpusdtClient:
    return request.app.state.epusdt


@app.post("/create-order")
async def create_order(request: Request):
    client = get_client(request)
    order = await client.create_order(
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
    client = get_client(request)
    try:
        callback = client.parse_gmpay_callback(payload)
    except SignatureError as exc:
        raise HTTPException(status_code=400, detail="签名错误") from exc

    if callback.status == OrderStatus.PAID:
        # 先验签再处理，并按 callback.order_id 做幂等去重，避免重复通知重复入账。
        pass

    return "ok"


@app.get("/notify/epay")
async def epay_notify(request: Request):
    params = dict(request.query_params)
    client = get_client(request)
    try:
        callback = client.parse_epay_callback(params)
    except SignatureError as exc:
        raise HTTPException(status_code=400, detail="签名错误") from exc

    if callback.trade_status == TradeStatus.TRADE_SUCCESS:
        # 先验签再处理，并按 callback.out_trade_no 做幂等去重。
        pass

    return "success"
