"""Shared pytest fixtures for Kosher tests."""

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def feature_file_factory(tmp_path: Path) -> Callable[[str, str], Path]:
    """Factory to create temp .feature files."""

    def create(name: str, content: str) -> Path:
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    return create
