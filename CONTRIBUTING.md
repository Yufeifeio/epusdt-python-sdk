# 参与开发

## 本地环境

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip build pytest
pip install -e .
```

## 运行测试

```bash
pytest
```

## 构建发布包

```bash
python -m build
```

## 说明

- `pip install epusdt` 面向使用 SDK 的接入方
- `pip install -e .` 面向本地开发、调试和提交改动
