import os
from time import time

from flask import Flask, jsonify, request

from epusdt import EpusdtClient, OrderStatus, SignatureError, TradeStatus


app = Flask(__name__)

client = EpusdtClient(
    base_url=os.environ["EPUSDT_BASE_URL"],
    pid=os.environ["EPUSDT_PID"],
    secret_key=os.environ["EPUSDT_SECRET_KEY"],
)


def mark_order_paid(*, order_id: str, trade_id: str, payload: dict) -> None:
    _ = (order_id, trade_id, payload)


@app.post("/create-order")
def create_order():
    order = client.create_order(
        order_id=f"FLASK_{int(time())}",
        amount=100,
        currency="cny",
        token="USDT",
        network="tron",
        notify_url="https://merchant.example.com/notify",
        redirect_url="https://merchant.example.com/return",
        name="会员充值",
    )
    return jsonify(
        {
            "trade_id": order.trade_id,
            "payment_url": order.payment_url,
            "actual_amount": order.actual_amount,
        }
    )


@app.post("/notify/gmpay")
def gmpay_notify():
    payload = request.get_json(silent=True) or {}
    try:
        callback = client.parse_gmpay_callback(payload)
    except SignatureError:
        return "fail", 400

    if callback.status == OrderStatus.PAID:
        mark_order_paid(
            order_id=callback.order_id,
            trade_id=callback.trade_id,
            payload=payload,
        )

    return "ok", 200


@app.get("/notify/epay")
def epay_notify():
    params = request.args.to_dict(flat=True)
    try:
        callback = client.parse_epay_callback(params)
    except SignatureError:
        return "fail", 400

    if callback.trade_status == TradeStatus.TRADE_SUCCESS:
        mark_order_paid(
            order_id=callback.out_trade_no,
            trade_id=callback.trade_no,
            payload=params,
        )

    return "success", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
