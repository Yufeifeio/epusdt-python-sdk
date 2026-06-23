from epusdt import EpusdtClient


client = EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
)

order = client.create_order(
    order_id="ORD202606240001",
    amount=100,
    currency="cny",
    token="usdt",
    network="tron",
    notify_url="https://merchant.example.com/notify",
    redirect_url="https://merchant.example.com/return",
    name="VIP",
)

print(order.trade_id)
print(order.payment_url)

