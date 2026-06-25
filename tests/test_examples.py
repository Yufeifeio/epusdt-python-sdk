"""对 examples/ 下的脚本做语法编译与基础烟测，确保示例与 SDK API 保持一致。

注意：示例里默认指向 https://pay.example.com，不会真正发起网络请求。
这里只做：
1. 全部示例语法可编译。
2. 不依赖 Web 框架的示例（basic / async / live_gateway_check）能被安全导入或解析。
3. live_gateway_check 在缺少环境变量时给出清晰报错而不是误打真实网关。
"""
from __future__ import annotations

import ast
import compileall
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"

ALL_EXAMPLES = sorted(EXAMPLES_DIR.glob("*.py"))


def test_examples_directory_present() -> None:
    assert ALL_EXAMPLES, "examples 目录不应为空"


@pytest.mark.parametrize("path", ALL_EXAMPLES, ids=lambda p: p.name)
def test_example_compiles(path: pathlib.Path) -> None:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    # 进一步用 AST 解析确认是合法模块。
    ast.parse(source)


def test_compileall_examples() -> None:
    assert compileall.compile_dir(str(EXAMPLES_DIR), quiet=1)


def test_callbacks_examples_verify_before_processing() -> None:
    # 回调示例必须先验签（parse_*_callback 默认 verify=True），再处理订单。
    for name in ("flask_example.py", "fastapi_example.py", "django_example.py"):
        text = (EXAMPLES_DIR / name).read_text(encoding="utf-8")
        assert "parse_gmpay_callback" in text
        assert "parse_epay_callback" in text
        assert "SignatureError" in text
        # 不应出现关闭验签的反面示例。
        assert "verify=False" not in text


def test_web_examples_return_official_ack_strings() -> None:
    flask = (EXAMPLES_DIR / "flask_example.py").read_text(encoding="utf-8")
    assert '"ok"' in flask and '"success"' in flask


def test_live_gateway_check_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy
    import sys

    for var in ("EPUSDT_BASE_URL", "EPUSDT_PID", "EPUSDT_SECRET_KEY", "EPUSDT_NOTIFY_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(sys, "argv", ["live_gateway_check.py"])
    with pytest.raises(SystemExit):
        runpy.run_path(str(EXAMPLES_DIR / "live_gateway_check.py"), run_name="__main__")
