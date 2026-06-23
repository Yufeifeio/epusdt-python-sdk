from epusdt import CheckoutOrder, CreateOrderResponse, OrderStatus, PaymentType


def test_create_order_response_datetime_property() -> None:
    order = CreateOrderResponse(
        trade_id="TRADE001",
        order_id="ORD001",
        amount=100,
        currency="CNY",
        actual_amount=14.29,
        receive_address="addr",
        token="USDT",
        status=OrderStatus.WAITING_PAYMENT,
        expiration_time=1779530812,
        payment_url="https://pay.example.com/pay/checkout-counter/TRADE001",
    )
    assert order.expiration_datetime.year >= 2026


def test_checkout_order_datetime_properties() -> None:
    checkout = CheckoutOrder(
        trade_id="TRADE001",
        amount=100,
        actual_amount=14.29,
        token="USDT",
        currency="CNY",
        receive_address="addr",
        network="tron",
        status=OrderStatus.WAITING_PAYMENT,
        payment_type=PaymentType.GMPAY,
        expiration_time=1779530812000,
        redirect_url="https://merchant.example/return",
        payment_url="",
        created_at=1779530212000,
        is_selected=False,
    )
    assert checkout.expiration_datetime.year >= 2026
    assert checkout.created_datetime.year >= 2026

