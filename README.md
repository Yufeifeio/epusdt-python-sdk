# Epusdt Python SDK

`epusdt` 的 Python SDK，接口按 `GMWalletApp/epusdt` 当前代码路由实现，对齐：

- `POST /payments/gmpay/v1/order/create-transaction`
- `GET /payments/gmpay/v1/config`
- `GET /pay/checkout-counter-resp/{trade_id}`
- `GET /pay/check-status/{trade_id}`
- `POST /pay/switch-network`
- `GET/POST /payments/epay/v1/order/create-transaction/submit.php`
- GMPay / EPay 两套回调验签

这个 SDK 的设计参考了 `luoyanglang/bepusdt-python-sdk` 的项目结构，但签名方式、接口路径、返回模型和 EPay 兼容逻辑都已经按 `GMWalletApp/epusdt` 的当前实现重新整理。

## 安装

从 GitHub 安装：

```bash
pip install git+https://github.com/Yufeifeio/epusdt-python-sdk.git
```

本地开发安装：

```bash
pip install -e .
```

## 核心差异

和旧的 `bepusdt`/`epusdt` 非官方 SDK 不同，这个版本基于当前 `GMWalletApp/epusdt` 实现：

- 使用 `pid + secret_key`，不是 `api_token`
- 创建订单主入口是 `GMPay v1`
- 支持创建 `status=4` 的占位订单
- 支持后续 `switch-network`
- 支持 `EPay submit.php` 重定向模式
- 支持 GMPay JSON 回调和 EPay GET 回调两种验签

## 快速开始

```python
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
```

## 占位订单

如果你要先创建订单，再让用户在收银台选择网络和币种：

```python
placeholder = client.create_order(
    order_id="ORD202606240002",
    amount=88.5,
    currency="cny",
    notify_url="https://merchant.example.com/notify",
)

print(placeholder.status)   # OrderStatus.WAITING_SELECTION
print(placeholder.trade_id)

selected = client.switch_network(
    trade_id=placeholder.trade_id,
    token="USDT",
    network="solana",
)
```

## EPay 兼容模式

构造 `submit.php` 跳转地址：

```python
url = client.build_epay_redirect_url(
    out_trade_no="ORD202606240003",
    money=100,
    notify_url="https://merchant.example.com/notify",
    return_url="https://merchant.example.com/return",
    name="VIP",
)

print(url)
```

也可以直接请求网关并拿到它返回的收银台地址：

```python
redirect = client.create_epay_order(
    out_trade_no="ORD202606240003",
    money=100,
    notify_url="https://merchant.example.com/notify",
    return_url="https://merchant.example.com/return",
)

print(redirect.checkout_url)
```

## 回调验签

GMPay JSON 回调：

```python
payload = {
    "pid": "1000",
    "trade_id": "20260523171652123456001",
    "order_id": "ORD202605230001",
    "amount": 100,
    "actual_amount": 14.29,
    "receive_address": "TTestTronAddress001",
    "token": "USDT",
    "block_transaction_id": "0xabc123",
    "status": 2,
    "signature": "a1b2c3",
}

callback = client.parse_gmpay_callback(payload)
print(callback.trade_id)
```

EPay GET 回调：

```python
params = {
    "pid": "1000",
    "trade_no": "20260523171652123456001",
    "out_trade_no": "ORD202605230001",
    "type": "alipay",
    "name": "VIP",
    "money": "100.0000",
    "trade_status": "TRADE_SUCCESS",
    "sign": "a1b2c3",
    "sign_type": "MD5",
}

callback = client.parse_epay_callback(params)
print(callback.out_trade_no)
```

## API 一览

- `create_order(...)`
- `get_public_config()`
- `get_checkout(trade_id)`
- `check_status(trade_id)`
- `switch_network(trade_id, token, network)`
- `build_epay_params(...)`
- `build_epay_redirect_url(...)`
- `create_epay_order(...)`
- `verify_gmpay_callback(payload)`
- `verify_epay_callback(params)`
- `parse_gmpay_callback(payload)`
- `parse_epay_callback(params)`

## 开发

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip build pytest
pip install -e .
pytest
python -m build
```

