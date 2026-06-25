"""同步客户端基础用法示例。

安全说明：
- 默认从环境变量读取网关地址与密钥，避免在源码里硬编码真实密钥；
- 没有配置环境变量时只打印提示并退出，不会误请求真实支付网关。

    export EPUSDT_BASE_URL="https://pay.your-domain.com"
    export EPUSDT_PID="1000"
    export EPUSDT_SECRET_KEY="your_secret_key"
    export EPUSDT_NOTIFY_URL="https://merchant.example.com/notify"
    python examples/basic_usage.py
"""
import os
from time import time

from epusdt import EpusdtClient


def main() -> None:
    base_url = os.getenv("EPUSDT_BASE_URL")
    pid = os.getenv("EPUSDT_PID")
    secret_key = os.getenv("EPUSDT_SECRET_KEY")
    notify_url = os.getenv("EPUSDT_NOTIFY_URL")

    if not all([base_url, pid, secret_key, notify_url]):
        print(
            "请先设置 EPUSDT_BASE_URL / EPUSDT_PID / EPUSDT_SECRET_KEY / EPUSDT_NOTIFY_URL "
            "环境变量后再运行本示例。"
        )
        return

    with EpusdtClient(base_url=base_url, pid=pid, secret_key=secret_key) as client:
        order = client.create_order(
            order_id=f"ORD{int(time())}",
            amount=100,
            currency="cny",
            token="USDT",
            network="tron",
            notify_url=notify_url,
            redirect_url=os.getenv("EPUSDT_REDIRECT_URL") or None,
            name="会员充值",
        )
        print(order.trade_id)
        print(order.payment_url)
        print(order.actual_amount)


if __name__ == "__main__":
    main()
