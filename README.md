# epusdt Python SDK

[![PyPI version](https://img.shields.io/pypi/v/epusdt.svg)](https://pypi.org/project/epusdt/)
[![Python versions](https://img.shields.io/pypi/pyversions/epusdt.svg)](https://pypi.org/project/epusdt/)
[![CI](https://github.com/Yufeifeio/epusdt-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Yufeifeio/epusdt-python-sdk/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/LICENSE)

适用于 `GMWalletApp/epusdt` 商户公开支付接口的 Python SDK，提供同步与异步两套客户端，支持 `GMPay` 下单、`EPay submit.php` 兼容接入、订单查询、回调验签和收款二维码生成。

当前版本只封装商户公开支付能力，不包含后台管理接口。

## 相关链接

- Epusdt 官方项目：[GMWalletApp/epusdt](https://github.com/GMWalletApp/epusdt)
- PyPI 页面：[epusdt](https://pypi.org/project/epusdt/)
- 更新日志：[CHANGELOG.md](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/CHANGELOG.md)
- 示例代码：[同步基础用法](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/basic_usage.py) / [异步基础用法](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/async_basic_usage.py) / [Flask](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/flask_example.py) / [FastAPI](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/fastapi_example.py) / [Django](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/django_example.py)

## 核心能力

- GMPay 创建订单
- 支付配置查询
- 收银台订单查询
- 支付状态查询
- 切换网络 / 币种
- 手动提交交易哈希补单
- EPay `submit.php` 兼容接入
- GMPay / EPay 回调验签
- 订单二维码生成
- 官方 `status_code` 业务错误码映射
- `Django` / `Flask` / `FastAPI` 接入示例

## 客户端选择

- `EpusdtClient`：适合同步 Web 项目、普通脚本、管理后台任务
- `AsyncEpusdtClient`：适合 `FastAPI`、异步任务队列、高并发接口服务

## 安装

直接安装：

```bash
pip install epusdt
```

需要二维码功能：

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

补充说明：

- `base_url` 推荐填写网关根地址，例如 `https://pay.example.com`
- 如果你手里只有 EPay 地址，也可以直接填写 `/payments/epay/v1/order/create-transaction` 或完整 `submit.php` 地址，SDK 会自动识别
- `amount` / `money` 支持 `int`、`float`、`Decimal` 和数字字符串
- 如果使用 EPay 兼容接口或 `payment_type="Epay"`，建议使用数字 `pid`

## 快速开始

### 同步客户端

```python
from epusdt import EpusdtClient

with EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
) as client:
    order = client.create_order(
        order_id="ORD202606240001",
        amount=100,
        currency="cny",
        token="USDT",
        network="tron",
        notify_url="https://merchant.example.com/notify",
        redirect_url="https://merchant.example.com/return",
        name="会员充值",
    )

    print(order.trade_id)
    print(order.payment_url)
    print(order.actual_amount)
```

### 异步客户端

```python
import asyncio

from epusdt import AsyncEpusdtClient


async def main() -> None:
    async with AsyncEpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
    ) as client:
        order = await client.create_order(
            order_id="ORD202606240099",
            amount=100,
            currency="cny",
            token="USDT",
            network="tron",
            notify_url="https://merchant.example.com/notify",
            redirect_url="https://merchant.example.com/return",
            name="会员充值",
        )

        print(order.trade_id)
        print(order.payment_url)


asyncio.run(main())
```

## 常见用法

以下示例默认已经初始化好 `client`。如果你使用异步客户端，对应方法前加 `await` 即可。

### 查询支付配置

```python
config = client.get_public_config()

for asset in config.supported_assets:
    print(asset.network, asset.tokens)
```

### 创建待选网络订单

```python
placeholder = client.create_order(
    order_id="ORD202606240002",
    amount=88.5,
    currency="cny",
    notify_url="https://merchant.example.com/notify",
)

selected = client.switch_network(
    trade_id=placeholder.trade_id,
    token="USDT",
    network="solana",
)

print(selected.trade_id)
print(selected.receive_address)
```

### 查询订单和支付状态

```python
checkout = client.get_checkout("20260523171652123456001")
status = client.check_status("20260523171652123456001")

print(checkout.payment_type)
print(status.status)
```

### EPay 兼容接入

构造跳转地址：

```python
url = client.build_epay_redirect_url(
    out_trade_no="ORD202606240003",
    money=100,
    notify_url="https://merchant.example.com/notify",
    return_url="https://merchant.example.com/return",
    name="会员充值",
)

print(url)
```

直接请求网关并获取收银台地址：

```python
redirect = client.create_epay_order(
    out_trade_no="ORD202606240003",
    money=100,
    notify_url="https://merchant.example.com/notify",
    return_url="https://merchant.example.com/return",
)

print(redirect.checkout_url)
```

### 手动补单

```python
result = client.submit_tx_hash(
    trade_id="20260523171652123456001",
    block_transaction_id="0xabc123",
)

print(result.status)
print(result.block_transaction_id)
```

### 回调验签

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
    "name": "会员充值",
    "money": "100.0000",
    "trade_status": "TRADE_SUCCESS",
    "sign": "a1b2c3",
    "sign_type": "MD5",
}

callback = client.parse_epay_callback(params)
print(callback.out_trade_no)
```

### 业务错误码捕获

SDK 已按官方 `status_code` 映射常见业务异常，商户侧可以直接按具体错误类型处理：

```python
from epusdt import (
    EpusdtClient,
    InvalidNotifyURLError,
    OrderExistsError,
    OrderNotFoundError,
)

client = EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
)

try:
    client.create_order(
        order_id="ORD202606240003",
        amount=100,
        currency="cny",
        notify_url="https://merchant.example.com/notify",
    )
except OrderExistsError:
    print("订单号重复")
except InvalidNotifyURLError:
    print("回调地址不合法")
except OrderNotFoundError:
    print("订单不存在")
```

### 生成二维码

```python
order = client.get_checkout("20260523171652123456001")

image = order.generate_qrcode()
image.save("epusdt-payment.png")
```

## Web 项目示例

- `examples/flask_example.py`：同步 Flask 接入示例
- `examples/fastapi_example.py`：异步 FastAPI 接入示例
- `examples/django_example.py`：Django 下单、GMPay 回调、EPay 回调完整模板

## 自动化流程

仓库内已提供 GitHub Actions：

- `CI`：自动运行多 Python 版本测试、构建和 `twine check`
- `Release`：手动触发发布，自动测试、构建、创建 GitHub Release，并可上传到 PyPI

发布到 PyPI 前，需要在 GitHub 仓库 `Secrets and variables / Actions` 中配置：

- `PYPI_API_TOKEN`

## 示例代码

- `examples/basic_usage.py`：基础下单示例
- `examples/async_basic_usage.py`：异步基础下单示例
- `examples/flask_example.py`：Flask 创建订单与回调处理示例
- `examples/fastapi_example.py`：FastAPI 异步创建订单与回调处理示例

## API 一览

- `EpusdtClient(...)`
- `AsyncEpusdtClient(...)`
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

## 适用范围

当前版本面向 `epusdt` 商户公开支付接口，适合以下接入场景：

- 服务端创建订单
- 前端收银台支付
- EPay 兼容接入
- 支付回调验签
- Flask / Django 等同步项目
- FastAPI / 异步任务队列项目

## 验证情况

- 单元测试通过
- 构建通过
- 干净虚拟环境安装通过
- 安装后导入通过
- 二维码功能烟测通过
- 已完成线上网关联调验证
- 同步与异步客户端都已覆盖测试

## 开发

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip build pytest
pip install -e .
pytest
python -m build
```
