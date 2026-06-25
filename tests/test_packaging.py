"""打包与元数据一致性检查（不依赖已构建的 dist）。"""
from __future__ import annotations

import pathlib

import epusdt

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_version_single_source_matches_pyproject() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # 版本号应当是单一来源（dynamic，从 epusdt._version 读取），
    # pyproject 里不应再硬编码 version = "x.y.z"。
    assert 'dynamic = ["version"]' in pyproject
    assert "epusdt._version" in pyproject
    assert epusdt.__version__
    # _version.py 与包暴露的版本一致。
    from epusdt import _version

    assert epusdt.__version__ == _version.__version__


def test_py_typed_is_packaged_in_source_tree() -> None:
    assert (PROJECT_ROOT / "epusdt" / "py.typed").is_file()


def test_package_name_matches_import_name() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "epusdt"' in pyproject
    assert epusdt.__name__ == "epusdt"


def test_license_and_readme_present() -> None:
    assert (PROJECT_ROOT / "LICENSE").is_file()
    assert (PROJECT_ROOT / "README.md").is_file()


def test_public_api_exports_are_importable() -> None:
    for name in epusdt.__all__:
        assert hasattr(epusdt, name), f"{name} 在 __all__ 中但未导出"


def test_both_clients_and_helpers_exported() -> None:
    for name in (
        "EpusdtClient",
        "AsyncEpusdtClient",
        "generate_gmpay_signature",
        "generate_epay_signature",
        "verify_gmpay_signature",
        "verify_epay_signature",
    ):
        assert name in epusdt.__all__
