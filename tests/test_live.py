"""真实网关联调测试。

默认跳过；只有同时设置了 EPUSDT_BASE_URL / EPUSDT_PID / EPUSDT_SECRET_KEY
环境变量时才会运行。运行方式：

    EPUSDT_BASE_URL=... EPUSDT_PID=... EPUSDT_SECRET_KEY=... pytest -m live
"""
from __future__ import annotations

import os

import pytest

from epusdt import EpusdtClient, PublicConfig

_REQUIRED = ("EPUSDT_BASE_URL", "EPUSDT_PID", "EPUSDT_SECRET_KEY")

pytestmark = pytest.mark.live

skip_reason = "未配置真实网关环境变量（EPUSDT_BASE_URL/EPUSDT_PID/EPUSDT_SECRET_KEY）"


@pytest.fixture
def live_client() -> EpusdtClient:
    if not all(os.getenv(k) for k in _REQUIRED):
        pytest.skip(skip_reason)
    return EpusdtClient(
        base_url=os.environ["EPUSDT_BASE_URL"],
        pid=os.environ["EPUSDT_PID"],
        secret_key=os.environ["EPUSDT_SECRET_KEY"],
    )


def test_live_public_config(live_client: EpusdtClient) -> None:
    with live_client as client:
        config = client.get_public_config()
        assert isinstance(config, PublicConfig)
