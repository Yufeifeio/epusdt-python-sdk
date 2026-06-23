import argparse
import json
import os
from time import time

from epusdt import EpusdtClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Epusdt 真实网关联调脚本")
    parser.add_argument("--base-url", default=os.getenv("EPUSDT_BASE_URL", ""), help="网关根地址")
    parser.add_argument("--pid", default=os.getenv("EPUSDT_PID", ""), help="商户 pid")
    parser.add_argument("--secret-key", default=os.getenv("EPUSDT_SECRET_KEY", ""), help="商户 secret_key")
    parser.add_argument("--notify-url", default=os.getenv("EPUSDT_NOTIFY_URL", ""), help="回调地址")
    parser.add_argument("--redirect-url", default=os.getenv("EPUSDT_REDIRECT_URL", ""), help="回跳地址")
    parser.add_argument("--amount", type=float, default=100.0, help="订单金额")
    parser.add_argument("--currency", default="cny", help="法币单位")
    parser.add_argument("--token", default="USDT", help="币种")
    parser.add_argument("--network", default="tron", help="网络")
    parser.add_argument("--name", default="联调测试订单", help="订单名称")
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="先创建待选网络订单，再调用 switch_network 选中网络",
    )
    return parser


def require_value(name: str, value: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SystemExit(f"缺少参数: {name}")
    return text


def main() -> None:
    args = build_parser().parse_args()
    base_url = require_value("base_url", args.base_url)
    pid = require_value("pid", args.pid)
    secret_key = require_value("secret_key", args.secret_key)
    notify_url = require_value("notify_url", args.notify_url)

    with EpusdtClient(
        base_url=base_url,
        pid=pid,
        secret_key=secret_key,
    ) as client:
        config = client.get_public_config()
        print("== public config ==")
        print(
            json.dumps(
                {
                    "version": config.version,
                    "supported_assets": [
                        {
                            "network": asset.network,
                            "display_name": asset.display_name,
                            "tokens": asset.tokens,
                        }
                        for asset in config.supported_assets
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        order_id = f"LIVE_{int(time())}"
        if args.placeholder:
            placeholder = client.create_order(
                order_id=order_id,
                amount=args.amount,
                currency=args.currency,
                notify_url=notify_url,
                redirect_url=args.redirect_url or None,
                name=args.name,
            )
            print("== placeholder order ==")
            print(json.dumps(placeholder.__dict__, ensure_ascii=False, indent=2, default=str))
            checkout = client.switch_network(
                trade_id=placeholder.trade_id,
                token=args.token,
                network=args.network,
            )
        else:
            order = client.create_order(
                order_id=order_id,
                amount=args.amount,
                currency=args.currency,
                token=args.token,
                network=args.network,
                notify_url=notify_url,
                redirect_url=args.redirect_url or None,
                name=args.name,
            )
            checkout = client.get_checkout(order.trade_id)

        print("== checkout ==")
        print(json.dumps(checkout.__dict__, ensure_ascii=False, indent=2, default=str))

        status = client.check_status(checkout.trade_id)
        print("== status ==")
        print(json.dumps(status.__dict__, ensure_ascii=False, indent=2, default=str))

        print("== callback helpers ==")
        print("GMPay / EPay 回调验签可结合 examples/django_example.py 使用。")


if __name__ == "__main__":
    main()
