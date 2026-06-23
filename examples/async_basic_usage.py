import asyncio
from time import time

from epusdt import AsyncEpusdtClient


async def main() -> None:
    async with AsyncEpusdtClient(
        base_url="https://pay.example.com",
        pid="1000",
        secret_key="epusdt_secret_key",
    ) as client:
        order = await client.create_order(
            order_id=f"ORD{int(time())}",
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


if __name__ == "__main__":
    asyncio.run(main())
