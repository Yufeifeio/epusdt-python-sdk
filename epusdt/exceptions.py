from __future__ import annotations

from typing import Any, Optional, Type


class EpusdtError(Exception):
    """SDK 基础异常。"""


class ValidationError(EpusdtError):
    """请求发出前的本地参数校验失败。"""


class SignatureError(EpusdtError):
    """回调验签失败。"""


class NetworkError(EpusdtError):
    """请求无法到达网关。"""


class RequestTimeoutError(EpusdtError):
    """请求网关超时。"""


class HTTPError(EpusdtError):
    """原始 HTTP 层异常。"""

    def __init__(
        self,
        message: str,
        *,
        http_status: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.response_text = response_text


class ClientError(HTTPError):
    """HTTP 4xx 或响应格式异常。"""


class AuthenticationError(ClientError):
    """签名认证失败或凭证不正确。"""


class ServerError(HTTPError):
    """HTTP 5xx 网关异常。"""


class APIError(EpusdtError):
    """网关返回的业务异常。"""

    def __init__(
        self,
        message: str,
        *,
        business_code: Optional[int] = None,
        http_status: Optional[int] = None,
        response: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.business_code = business_code
        self.http_status = http_status
        self.response = response
        self.request_id = request_id


class SystemAPIError(APIError):
    """系统错误或普通参数错误。"""


class OrderExistsError(APIError):
    """商户订单已存在。"""


class NoAvailableWalletError(APIError):
    """无可用钱包地址。"""


class InvalidAmountError(APIError):
    """支付金额不符合要求。"""


class NoAvailableAmountChannelError(APIError):
    """无可用金额通道。"""


class RateCalculationError(APIError):
    """汇率计算失败。"""


class TransactionAlreadyProcessedError(APIError):
    """链上交易已处理。"""


class OrderNotFoundError(APIError):
    """订单不存在。"""


class RequestParamsError(APIError):
    """网关无法解析请求参数。"""


class OrderStatusChangedError(APIError):
    """订单状态已变化。"""


class SubOrderLimitExceededError(APIError):
    """超过子订单数量上限。"""


class SubOrderSwitchNotAllowedError(APIError):
    """子订单不允许切换网络。"""


class OrderNotAwaitingPaymentError(APIError):
    """订单当前不是待支付状态。"""


class ChainNotEnabledError(APIError):
    """链未启用。"""


class SupportedAssetNotFoundError(APIError):
    """币种或网络组合不存在。"""


class PaymentProviderNotEnabledError(APIError):
    """支付服务商未启用。"""


class PaymentProviderConfigError(APIError):
    """支付服务商配置不完整。"""


class PaymentProviderUnsupportedError(APIError):
    """支付服务商不支持该网络或币种。"""


class ManualPaymentVerifyError(APIError):
    """手动补单校验失败。"""


class ManualPaymentProviderError(APIError):
    """手动补单不支持当前支付类型。"""


class InvalidNotifyURLError(APIError):
    """回调地址不合法。"""


class PaymentProviderCreateError(APIError):
    """支付服务商创建订单失败。"""


class InvalidRedirectURLError(APIError):
    """订单回跳地址不合法。"""


class OrderApiKeyUnavailableError(APIError):
    """订单对应 API Key 不可用。"""


class EPayReturnSignatureBuildError(APIError):
    """生成 EPay 返回签名失败。"""


ERROR_CODE_MAP: dict[int, Type[APIError]] = {
    400: SystemAPIError,
    10002: OrderExistsError,
    10003: NoAvailableWalletError,
    10004: InvalidAmountError,
    10005: NoAvailableAmountChannelError,
    10006: RateCalculationError,
    10007: TransactionAlreadyProcessedError,
    10008: OrderNotFoundError,
    10009: RequestParamsError,
    10010: OrderStatusChangedError,
    10011: SubOrderLimitExceededError,
    10012: SubOrderSwitchNotAllowedError,
    10013: OrderNotAwaitingPaymentError,
    10014: ChainNotEnabledError,
    10016: SupportedAssetNotFoundError,
    10017: PaymentProviderNotEnabledError,
    10018: PaymentProviderConfigError,
    10019: PaymentProviderUnsupportedError,
    10038: ManualPaymentVerifyError,
    10039: ManualPaymentProviderError,
    10041: InvalidNotifyURLError,
    10042: PaymentProviderCreateError,
    10044: InvalidRedirectURLError,
    10045: OrderApiKeyUnavailableError,
    10046: EPayReturnSignatureBuildError,
}


def create_api_error(
    message: str,
    *,
    business_code: Optional[int] = None,
    http_status: Optional[int] = None,
    response: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> APIError:
    exc_cls = APIError if business_code is None else ERROR_CODE_MAP.get(business_code, APIError)
    return exc_cls(
        message,
        business_code=business_code,
        http_status=http_status,
        response=response,
        request_id=request_id,
    )
