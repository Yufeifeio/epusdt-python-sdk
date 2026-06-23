from time import time

from flask import Flask, jsonify, request

from epusdt import EpusdtClient, OrderStatus, SignatureError, TradeStatus


app = Flask(__name__)

client = EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
)


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
        # 在这里写你自己的订单处理逻辑
        pass

    return "ok", 200


@app.get("/notify/epay")
def epay_notify():
    params = request.args.to_dict(flat=True)
    try:
        callback = client.parse_epay_callback(params)
    except SignatureError:
        return "fail", 400

    if callback.trade_status == TradeStatus.TRADE_SUCCESS:
        # 在这里写你自己的订单处理逻辑
        pass

    return "success", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
