"""异步客户端基础用法示例。"""
import asyncio
import os
from time import time

from epusdt import AsyncEpusdtClient


async def main() -> None:
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

    async with AsyncEpusdtClient(base_url=base_url, pid=pid, secret_key=secret_key) as client:
        order = await client.create_order(
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


if __name__ == "__main__":
    asyncio.run(main())
