from epusdt import CheckoutOrder, CreateOrderResponse, Network, OrderStatus, PaymentType, Token


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


def test_official_network_and_token_enums() -> None:
    assert Network.TRON.value == "tron"
    assert Network.SOLANA.value == "solana"
    assert Network.ETHEREUM.value == "ethereum"
    assert Network.BSC.value == "bsc"
    assert Network.POLYGON.value == "polygon"
    assert Network.PLASMA.value == "plasma"
    assert Network.TON.value == "ton"
    assert Network.APTOS.value == "aptos"

    assert Token.USDT.value == "USDT"
    assert Token.TRX.value == "TRX"
    assert Token.USDC.value == "USDC"
    assert Token.USDC_E.value == "USDC.e"
    assert Token.SOL.value == "SOL"
    assert Token.TON.value == "TON"


def test_official_default_supported_assets_snapshot() -> None:
    expected = {
        Network.TRON.value: [Token.TRX.value, Token.USDT.value],
        Network.ETHEREUM.value: [Token.USDT.value, Token.USDC.value],
        Network.SOLANA.value: [Token.USDT.value, Token.USDC.value, Token.SOL.value],
        Network.BSC.value: [Token.USDT.value, Token.USDC.value],
        Network.POLYGON.value: [Token.USDT.value, Token.USDC.value, Token.USDC_E.value],
        Network.PLASMA.value: [Token.USDT.value],
        Network.TON.value: [Token.TON.value, Token.USDT.value],
        Network.APTOS.value: [Token.USDC.value, Token.USDT.value],
    }
    assert expected[Network.TRON.value] == ["TRX", "USDT"]
    assert expected[Network.POLYGON.value] == ["USDT", "USDC", "USDC.e"]
    assert expected[Network.TON.value] == ["TON", "USDT"]
    assert expected[Network.APTOS.value] == ["USDC", "USDT"]
