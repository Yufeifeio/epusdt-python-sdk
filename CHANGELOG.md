# 更新日志

## v0.3.0

> 本版本包含两处与官方对齐的**兼容性修复**和一处**支付安全行为变更**，建议所有用户升级。

- **修复（重要）**：`Network.BSC` 的链标识由 `"bsc"` 更正为官方实际使用的 `"binance"`。
  之前使用 `Network.BSC` 下单会因链校验失败而报错。
- **修复（重要）**：签名串排序改为对拼接后的 `key=value` 整体排序，与官方 Go
  `sort.Strings` 字节级一致；修复自定义/插件参数在特定前缀场景下的签名不一致风险。
- **行为变更（支付安全）**：创建订单、切换网络、手动补单、EPay 下单等**非幂等写操作
  默认不再自动重试**，避免超时后重复下单。只有幂等的 GET 查询仍按 `max_retries` 重试。
- 新增：异步客户端 `close()` 别名（等价于 `aclose()`），与同步客户端命名保持一致。
- 健壮性：响应缺失或 `data` 字段类型异常时抛出明确的 `ClientError`，不再是裸 `KeyError`。
- 工程：版本号改为单一来源（从 `epusdt._version` 动态读取）；补充 `ruff`/`mypy`/`bandit`
  配置；测试覆盖率提升至 95%（新增签名、异常、打包、示例、Mock 网关与金额边界测试）。
- 示例：`basic_usage` / `async_basic_usage` 改为从环境变量读取配置，缺省时不再误请求网关；
  Flask / FastAPI / Django 示例改为从环境变量读取密钥并补充幂等与防重复通知说明。

## v0.2.8

- 顶层导出补齐 `HTTPError`、`SupportedAssetNotFoundError`
- 增加官方默认支持矩阵与自定义代币场景测试
- 增加 `live_gateway_check.py` 真实网关联调脚本

## v0.2.7

- SDK 枚举补齐官方源码已确认的 `Aptos`、`TON`、`USDC.e`
- 移除不准确的 `Network.OKPAY` 枚举项
- README 改为基于官方源码整理的默认支持矩阵说明
- 补充“可直接传入自定义代币字符串”的使用说明

## v0.2.6

- 新增官方 `status_code` 对应的细粒度异常类型
- 同步与异步客户端统一支持业务错误码映射与 `request_id`
- 新增 `Django` 接入示例，包含下单、GMPay 回调和 EPay 回调模板
- 新增 GitHub Actions 自动测试、自动构建和手动发布流程
- README 补充异常捕获示例、Django 示例入口和发布流程说明

## v0.2.5

- 新增 `AsyncEpusdtClient`
- 新增异步重试逻辑
- 新增异步基础示例
- FastAPI 示例改为真正的异步客户端接入方式
- README / PyPI 首页补充同步与异步客户端说明

## v0.2.4

- `base_url` 支持直接填写 EPay 创建订单地址或完整 `submit.php` 地址
- `amount` / `money` 新增数字字符串兼容
- `status_code` 兼容字符串形式返回值
- 增加客户端 `close()` 与上下文管理支持
- README 删除冗余入口并补充接入细节说明

## v0.2.3

- 增加 `CHANGELOG.md`
- 增加 Flask 接入示例
- 增加 FastAPI 接入示例
- README 补充官方项目、PyPI、更新日志和示例入口
- 统一版本号与用户代理标识

## v0.2.2

- README 首页重新排版，更适合 GitHub 与 PyPI 展示
- 顶部增加 PyPI、Python 版本、License 徽章
- 调整仓库描述、Homepage 和 Topics

## v0.2.1

- README 重写为更适合作为正式 PyPI 首页的中文版本
- 安装说明改为已发布到 PyPI 的真实状态
- 重新整理特性、常见用法、适用说明和验证情况

## v0.2.0

- 包元数据名称调整为 `epusdt`
- 增加二维码可选依赖
- 增加 `submit-tx-hash` 接口封装
- 增加订单二维码生成功能
- README 全面改为中文说明
