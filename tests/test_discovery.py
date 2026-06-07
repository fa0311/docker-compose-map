from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest

from docker_compose_map.discovery import select_compose_files

ASSETS = Path(__file__).parent / "assets"


def copy_asset(name: str, tmp_path: Path) -> Path:
    destination = tmp_path / name
    copytree(ASSETS / name, destination)
    return destination


def test_directory_input_uses_shallowest_compose_per_top_level(tmp_path: Path) -> None:
    repo = copy_asset("discovery", tmp_path)

    selection = select_compose_files((str(repo),))

    assert selection.root == repo
    assert selection.files == (repo / "stack" / "compose.yaml",)


def test_missing_glob_crashes_loudly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="matched no files"):
        select_compose_files((str(tmp_path / "missing" / "**" / "compose.yml"),))
