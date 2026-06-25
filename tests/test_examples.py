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
    ast.parse(source)


def test_compileall_examples() -> None:
    assert compileall.compile_dir(str(EXAMPLES_DIR), quiet=1)


def test_callbacks_examples_verify_before_processing() -> None:
    for name in ("flask_example.py", "fastapi_example.py", "django_example.py"):
        text = (EXAMPLES_DIR / name).read_text(encoding="utf-8")
        assert "parse_gmpay_callback" in text
        assert "parse_epay_callback" in text
        assert "SignatureError" in text
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
