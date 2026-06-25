from __future__ import annotations

import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"


@pytest.fixture
def project_root() -> pathlib.Path:
    return PROJECT_ROOT


@pytest.fixture
def examples_dir() -> pathlib.Path:
    return EXAMPLES_DIR
