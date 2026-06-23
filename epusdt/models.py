from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Mapping


class OrderStatus(IntEnum):
    WAITING_PAYMENT = 1
    PAID = 2
    EXPIRED = 3
    WAITING_SELECTION = 4


class PaymentType(str, Enum):
    GMPAY = "gmpay"
    EPAY = "epay"


class TradeStatus(str, Enum):
    TRADE_SUCCESS = "TRADE_SUCCESS"


class Network(str, Enum):
    TRON = "tron"
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    PLASMA = "plasma"
    TON = "ton"
    APTOS = "aptos"


class Token(str, Enum):
    USDT = "USDT"
    TRX = "TRX"
    USDC = "USDC"
    USDC_E = "USDC.e"
    SOL = "SOL"
    TON = "TON"


class _QRCodeMixin:
    def _qrcode_payload(self) -> str:
        receive_address = str(getattr(self, "receive_address", "") or "").strip()
        payment_url = str(getattr(self, "payment_url", "") or "").strip()
        if receive_address:
            return receive_address
        if payment_url:
            return payment_url
        raise ValueError("no receive_address or payment_url available for QR code generation")

    def generate_qrcode(self, box_size: int = 10, border: int = 4) -> Any:
        try:
            import qrcode
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "二维码功能需要先安装可选依赖: pip install epusdt[qrcode]"
            ) from exc

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(self._qrcode_payload())
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def get_qrcode_base64(self, box_size: int = 10, border: int = 4, format: str = "PNG") -> str:
        image = self.generate_qrcode(box_size=box_size, border=border)
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def get_qrcode_data_uri(self, box_size: int = 10, border: int = 4) -> str:
        return f"data:image/png;base64,{self.get_qrcode_base64(box_size=box_size, border=border)}"


@dataclass
class SupportedAsset:
    network: str
    display_name: str
    tokens: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SupportedAsset":
        return cls(
            network=str(data.get("network", "")),
            display_name=str(data.get("display_name", "")),
            tokens=[str(item) for item in data.get("tokens", [])],
        )


@dataclass
class SiteConfig:
    cashier_name: str = ""
    logo_url: str = ""
    website_title: str = ""
    support_link: str = ""
    background_color: str = ""
    background_image_url: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SiteConfig":
        return cls(
            cashier_name=str(data.get("cashier_name", "")),
            logo_url=str(data.get("logo_url", "")),
            website_title=str(data.get("website_title", "")),
            support_link=str(data.get("support_link", "")),
            background_color=str(data.get("background_color", "")),
            background_image_url=str(data.get("background_image_url", "")),
        )


@dataclass
class EpayDefaults:
    default_token: str = ""
    default_currency: str = ""
    default_network: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpayDefaults":
        return cls(
            default_token=str(data.get("default_token", "")),
            default_currency=str(data.get("default_currency", "")),
            default_network=str(data.get("default_network", "")),
        )


@dataclass
class OkpayConfig:
    enabled: bool = False
    allow_tokens: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OkpayConfig":
        return cls(
            enabled=bool(data.get("enabled", False)),
            allow_tokens=[str(item) for item in data.get("allow_tokens", [])],
        )


@dataclass
class PublicConfig:
    supported_assets: list[SupportedAsset]
    site: SiteConfig
    epay: EpayDefaults
    okpay: OkpayConfig
    version: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PublicConfig":
        return cls(
            supported_assets=[
                SupportedAsset.from_dict(item) for item in data.get("supported_assets", [])
            ],
            site=SiteConfig.from_dict(data.get("site", {})),
            epay=EpayDefaults.from_dict(data.get("epay", {})),
            okpay=OkpayConfig.from_dict(data.get("okpay", {})),
            version=str(data.get("version", "")),
        )


@dataclass
class CreateOrderResponse(_QRCodeMixin):
    trade_id: str
    order_id: str
    amount: float
    currency: str
    actual_amount: float
    receive_address: str
    token: str
    status: OrderStatus
    expiration_time: int
    payment_url: str

    @property
    def expiration_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.expiration_time, tz=timezone.utc)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CreateOrderResponse":
        return cls(
            trade_id=str(data["trade_id"]),
            order_id=str(data["order_id"]),
            amount=float(data["amount"]),
            currency=str(data["currency"]),
            actual_amount=float(data["actual_amount"]),
            receive_address=str(data.get("receive_address", "")),
            token=str(data.get("token", "")),
            status=OrderStatus(int(data["status"])),
            expiration_time=int(data["expiration_time"]),
            payment_url=str(data.get("payment_url", "")),
        )


@dataclass
class CheckoutOrder(_QRCodeMixin):
    trade_id: str
    amount: float
    actual_amount: float
    token: str
    currency: str
    receive_address: str
    network: str
    status: OrderStatus
    payment_type: PaymentType
    expiration_time: int
    redirect_url: str
    payment_url: str
    created_at: int
    is_selected: bool

    @property
    def expiration_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.expiration_time / 1000, tz=timezone.utc)

    @property
    def created_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.created_at / 1000, tz=timezone.utc)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CheckoutOrder":
        return cls(
            trade_id=str(data["trade_id"]),
            amount=float(data["amount"]),
            actual_amount=float(data["actual_amount"]),
            token=str(data.get("token", "")),
            currency=str(data.get("currency", "")),
            receive_address=str(data.get("receive_address", "")),
            network=str(data.get("network", "")),
            status=OrderStatus(int(data["status"])),
            payment_type=PaymentType(str(data["payment_type"]).lower()),
            expiration_time=int(data["expiration_time"]),
            redirect_url=str(data.get("redirect_url", "")),
            payment_url=str(data.get("payment_url", "")),
            created_at=int(data["created_at"]),
            is_selected=bool(data.get("is_selected", False)),
        )


@dataclass
class CheckStatusResponse:
    trade_id: str
    status: OrderStatus

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CheckStatusResponse":
        return cls(
            trade_id=str(data["trade_id"]),
            status=OrderStatus(int(data["status"])),
        )


@dataclass
class ManualPaymentResponse:
    trade_id: str
    status: OrderStatus
    block_transaction_id: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ManualPaymentResponse":
        return cls(
            trade_id=str(data["trade_id"]),
            status=OrderStatus(int(data["status"])),
            block_transaction_id=str(data["block_transaction_id"]),
        )


@dataclass
class GmpayCallback:
    pid: str
    trade_id: str
    order_id: str
    amount: float
    actual_amount: float
    receive_address: str
    token: str
    block_transaction_id: str
    status: OrderStatus
    signature: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GmpayCallback":
        return cls(
            pid=str(data["pid"]),
            trade_id=str(data["trade_id"]),
            order_id=str(data["order_id"]),
            amount=float(data["amount"]),
            actual_amount=float(data["actual_amount"]),
            receive_address=str(data.get("receive_address", "")),
            token=str(data.get("token", "")),
            block_transaction_id=str(data.get("block_transaction_id", "")),
            status=OrderStatus(int(data["status"])),
            signature=str(data["signature"]),
        )


@dataclass
class EpayCallback:
    pid: int
    trade_no: str
    out_trade_no: str
    type: str
    name: str
    money: str
    trade_status: TradeStatus
    sign: str
    sign_type: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpayCallback":
        return cls(
            pid=int(data["pid"]),
            trade_no=str(data["trade_no"]),
            out_trade_no=str(data["out_trade_no"]),
            type=str(data.get("type", "")),
            name=str(data.get("name", "")),
            money=str(data.get("money", "")),
            trade_status=TradeStatus(str(data["trade_status"])),
            sign=str(data["sign"]),
            sign_type=str(data.get("sign_type", "")),
        )


@dataclass
class EPayRedirectResponse:
    status_code: int
    location: str
    checkout_url: str
    params: dict[str, str]
