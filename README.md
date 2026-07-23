# EPUSDT Python SDK ✨

[![PyPI version](https://img.shields.io/pypi/v/epusdt?label=PyPI&cacheSeconds=60&v=0.4.0)](https://pypi.org/project/epusdt/)
[![Python versions](https://img.shields.io/pypi/pyversions/epusdt?label=Python&cacheSeconds=300)](https://pypi.org/project/epusdt/)
[![CI](https://github.com/Yufeifeio/epusdt-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Yufeifeio/epusdt-python-sdk/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/LICENSE)

适用于 `GMWalletApp/epusdt` 商户公开支付接口的 Python SDK，提供同步与异步两套客户端，覆盖 `GMPay` 下单、`EPay submit.php` 兼容接入、订单查询、回调验签和收款二维码生成。

当前版本只封装商户公开支付能力，不包含后台管理接口。

## 🔗 相关链接

- Epusdt 官方项目：[GMWalletApp/epusdt](https://github.com/GMWalletApp/epusdt)
- PyPI 页面：[epusdt](https://pypi.org/project/epusdt/)
- 更新日志：[CHANGELOG.md](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/CHANGELOG.md)
- 示例代码：[同步基础用法](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/basic_usage.py) / [异步基础用法](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/async_basic_usage.py) / [Flask](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/flask_example.py) / [FastAPI](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/fastapi_example.py) / [Django](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/examples/django_example.py)

## ✨ 核心能力

- GMPay 创建订单
- GMPay HMAC-SHA256 签名
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

## 🌐 官方支持矩阵

默认启用网络（括号内为接口实际使用的 `network` 取值）：

- `Tron`（`tron`）
- `Ethereum`（`ethereum`）
- `Solana`（`solana`）
- `BSC`（`binance`）
- `Polygon`（`polygon`）
- `Plasma`（`plasma`）
- `TON`（`ton`）
- `Aptos`（`aptos`）

官方默认内置币种：

- `Tron`：`USDT`、`TRX`
- `Ethereum`：`USDT`、`USDC`
- `Solana`：`USDT`、`USDC`、`SOL`
- `BSC`：`USDT`、`USDC`
- `Polygon`：`USDT`、`USDC`、`USDC.e`
- `Plasma`：`USDT`
- `TON`：`TON`、`USDT`
- `Aptos`：`USDC`、`USDT`

## ⚙️ 客户端选择

- `EpusdtClient`：适合同步 Web 项目、普通脚本、管理后台任务
- `AsyncEpusdtClient`：适合 `FastAPI`、异步任务队列、高并发接口服务

## 📦 安装

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

## 🧩 内置枚举

SDK 内置了一组和官方默认支持矩阵对应的常用枚举：

- `Network`：`TRON`、`SOLANA`、`ETHEREUM`、`BSC`、`POLYGON`、`PLASMA`、`TON`、`APTOS`
- `Token`：`USDT`、`USDC`、`USDC_E`、`TRX`、`SOL`、`TON`

## 🚀 快速开始

### 同步客户端

```python
from epusdt import EpusdtClient, Network, Token

with EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
) as client:
    order = client.create_order(
        order_id="ORD202606240001",
        amount=100,
        currency="cny",
        token=Token.USDT,
        network=Network.TRON,
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

from epusdt import AsyncEpusdtClient, Network, Token


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
            token=Token.USDT,
            network=Network.TRON,
            notify_url="https://merchant.example.com/notify",
            redirect_url="https://merchant.example.com/return",
            name="会员充值",
        )

        print(order.trade_id)
        print(order.payment_url)


asyncio.run(main())
```

## 🛠️ 常见用法

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

指定 EPay `type` selector：

```python
from epusdt import Network, Token, build_epay_type_selector

url = client.build_epay_redirect_url(
    out_trade_no="ORD202606240004",
    money=100,
    notify_url="https://merchant.example.com/notify",
    type=build_epay_type_selector(Token.USDT, Network.TRON),
)
```

官方 EPay 入口的 `type` 支持空值、`alipay`，或当前网关已启用资产的
`token.network` selector，例如 `usdt.tron`。selector 会优先确定本次订单的
`token/network`；如果要接入 `USDC.e` 这类币种名本身带点的资产，请继续使用
`token` 和 `network` 参数。

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

EPay 回调里的 `callback.type` 可能是 `alipay`，也可能是 `usdt.tron` 这类 selector。

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

二维码功能需要可选依赖：`pip install epusdt[qrcode]`。未安装时调用 `generate_qrcode()`
会抛出带安装提示的 `ImportError`。

## ⏱️ 超时与重试

```python
client = EpusdtClient(
    base_url="https://pay.example.com",
    pid="1000",
    secret_key="epusdt_secret_key",
    timeout=30.0,      # 单次请求超时（秒）
    max_retries=2,     # 仅作用于幂等 GET 查询
    retry_delay=0.5,   # 首次重试间隔，按指数退避
)
```

**支付安全重要说明**：

- **创建订单 / 切换网络 / 手动补单 / EPay 下单等非幂等写操作默认不会自动重试。**
  因为请求超时时服务端可能已经建单，自动重试会造成重复下单。
- 只有 `get_public_config` / `get_checkout` / `check_status` 这类幂等 GET 查询会按
  `max_retries` 自动重试（针对超时、网络错误、5xx）。
- 创建订单超时后，请用相同 `order_id` 调用 `get_checkout` / `check_status` 确认订单是否
  已经创建，再决定是否重试，切勿盲目换号重试。

## 💰 金额格式说明

- `amount` / `money` 接受 `int`、`float`、`str`、`Decimal`，金额必须 **大于 0.01**。
- 为避免浮点误差，**推荐使用字符串或 `Decimal` 传入金额**，例如 `amount="100.00"`。
- 签名与请求体的金额字符串严格一致：SDK 会按官方 Go 的
  `strconv.FormatFloat(f,'f',-1,64)` 规则去除末尾多余的 0（`100.50` → `100.5`，
  `100.00` → `100`），保证签名与官方一致。
- 不接受 `bool`，也会拒绝 `NaN` / `Infinity`。

## 🔒 安全注意事项

- **不要泄露 `secret_key`**：不要写进前端、日志或版本库；建议用环境变量管理。
- **签名算法要区分接口**：GMPay 使用 HMAC-SHA256，EPay 兼容接口使用 MD5。
- **回调必须先验签再处理**：始终通过 `parse_gmpay_callback` / `parse_epay_callback`
  （默认 `verify=True`）验证签名，不要直接信任未验签的回调参数。
- **订单处理必须幂等**：按 `order_id` / `out_trade_no` 去重，防止重复通知导致重复入账。
- **回调要返回官方约定的应答**：GMPay/EPay 回调成功后需返回 `ok` 或 `success`，
  否则网关会按退避策略重复通知。
- SDK 自身不会在日志或异常里打印 `secret_key`。

## 🧬 接口范围

- 覆盖 `GMWalletApp/epusdt` 商户公开支付接口：
  GMPay 下单、支付配置、收银台查询、支付状态、切换网络、手动补单、
  EPay `submit.php` 兼容下单，以及 GMPay / EPay 回调验签。
- **不包含**后台管理（`/admin/api/v1/...`）接口，仅面向商户收款接入。

## ✅ 验证情况

- 单元测试通过
- `ruff` / `mypy` / `bandit` 静态检查通过
- `python -m build` 与 `twine check` 通过
- wheel / sdist 干净虚拟环境安装并导入通过
- 二维码可选依赖烟测通过
- 同步与异步客户端均已覆盖测试

## 🔧 参与开发

本地开发、测试和构建说明见 [CONTRIBUTING.md](https://github.com/Yufeifeio/epusdt-python-sdk/blob/main/CONTRIBUTING.md)。
