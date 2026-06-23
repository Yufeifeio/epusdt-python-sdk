# Epusdt Python SDK

`epusdt` 的 Python SDK，面向 `GMWalletApp/epusdt` 商户接入场景。

适用于这些公开支付能力：

- GMPay 创建订单
- 支付配置查询
- 收银台订单查询
- 支付状态查询
- 切换网络 / 币种
- 手动提交交易哈希补单
- EPay `submit.php` 兼容接入
- GMPay / EPay 回调验签
- 订单二维码生成

## 安装

直接从 PyPI 安装：

```bash
pip install epusdt
```

如果需要二维码功能：

```bash
pip install epusdt[qrcode]
```

升级到最新版：

```bash
pip install --upgrade epusdt
```

本地开发安装：

```bash
pip install -e .
```

## 特性

- 对齐当前 `GMWalletApp/epusdt` 公开支付接口
- 使用 `pid + secret_key` 签名
- 支持 GMPay 主下单流程
- 支持 `status=4` 占位订单
- 支持后续 `switch-network`
- 支持 `submit-tx-hash` 手动补单
- 支持 EPay 兼容接入
- 支持 GMPay / EPay 两套回调验签
- 支持二维码可选依赖
- 支持打包安装、PyPI 分发和类型提示

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
print(order.actual_amount)
```

## 常见用法

### 1. 查询支付配置

```python
config = client.get_public_config()

for asset in config.supported_assets:
    print(asset.network, asset.tokens)
```

### 2. 创建占位订单，再让用户选网络

```python
placeholder = client.create_order(
    order_id="ORD202606240002",
    amount=88.5,
    currency="cny",
    notify_url="https://merchant.example.com/notify",
)

print(placeholder.trade_id)
print(placeholder.status)

selected = client.switch_network(
    trade_id=placeholder.trade_id,
    token="USDT",
    network="solana",
)

print(selected.trade_id)
print(selected.receive_address)
```

### 3. 查询收银台订单和支付状态

```python
checkout = client.get_checkout("20260523171652123456001")
status = client.check_status("20260523171652123456001")

print(checkout.payment_type)
print(status.status)
```

### 4. EPay 兼容接入

构造跳转地址：

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

直接请求网关并拿到收银台地址：

```python
redirect = client.create_epay_order(
    out_trade_no="ORD202606240003",
    money=100,
    notify_url="https://merchant.example.com/notify",
    return_url="https://merchant.example.com/return",
)

print(redirect.checkout_url)
```

### 5. 手动提交交易哈希补单

```python
result = client.submit_tx_hash(
    trade_id="20260523171652123456001",
    block_transaction_id="0xabc123",
)

print(result.status)
print(result.block_transaction_id)
```

### 6. 回调验签

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

### 7. 生成二维码

```python
order = client.get_checkout("20260523171652123456001")

image = order.generate_qrcode()
image.save("epusdt-payment.png")

base64_data = order.get_qrcode_base64()
data_uri = order.get_qrcode_data_uri()
```

## API 一览

- `create_order(...)`
- `get_public_config()`
- `get_checkout(trade_id)`
- `check_status(trade_id)`
- `switch_network(trade_id, token, network)`
- `submit_tx_hash(trade_id, block_transaction_id)`
- `build_epay_params(...)`
- `build_epay_redirect_url(...)`
- `create_epay_order(...)`
- `verify_gmpay_callback(payload)`
- `verify_epay_callback(params)`
- `parse_gmpay_callback(payload)`
- `parse_epay_callback(params)`

## 适用说明

这个 SDK 当前针对 `GMWalletApp/epusdt` 的商户公开支付接口，不包含后台管理端 `/admin/api/v1/...` 的封装。

如果你的目标是商户收款接入，这个 SDK 就是当前应该使用的版本。

## 验证情况

- 单元测试通过
- 构建通过
- 干净虚拟环境安装通过
- 安装后导入通过
- 二维码烟测通过
- 已发布到 PyPI

## 开发

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip build pytest
pip install -e .
pytest
python -m build
```
