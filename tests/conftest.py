from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from shutil import copytree

import pytest

ASSETS = Path(__file__).parent / "assets"


@pytest.fixture
def copy_asset(tmp_path: Path) -> Callable[[str], Path]:
    def copy(name: str) -> Path:
        destination = tmp_path / name
        copytree(ASSETS / name, destination)
        return destination

    return copy


@pytest.fixture
def assets() -> Path:
    return ASSETS
