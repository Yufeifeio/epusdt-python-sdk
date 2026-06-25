# 参与开发

## 本地环境

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## 运行测试与检查

```bash
pytest -q
pytest --cov=epusdt --cov-report=term-missing
ruff check epusdt tests examples
mypy epusdt
bandit -r epusdt
```

真实网关联调（默认跳过，需配置环境变量）：

```bash
EPUSDT_BASE_URL=... EPUSDT_PID=... EPUSDT_SECRET_KEY=... pytest -m live
```

## 构建发布包

```bash
python -m build
python -m twine check dist/*
```

## 发布清单（Release Checklist）

1. 修改 **唯一的版本来源** `epusdt/_version.py`（`pyproject.toml` 通过 `dynamic` 自动读取）。
2. 更新 `CHANGELOG.md`。
3. `pytest` 全绿、覆盖率 ≥90%、`ruff`/`mypy`/`bandit` 通过。
4. `python -m build && twine check dist/*` 通过。
5. 在干净虚拟环境验证 `pip install dist/*.whl` 后可 `import epusdt`。
6. 通过 GitHub Actions `Release` workflow 发布（`version` 输入需与 `_version.py` 一致）。
   - PyPI 上传使用 `secrets.PYPI_API_TOKEN`。

## 说明

- `pip install epusdt` 面向使用 SDK 的接入方
- `pip install -e .` 面向本地开发、调试和提交改动
