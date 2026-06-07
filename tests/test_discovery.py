from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from docker_compose_map.discovery import select_compose_files


def test_directory_input_uses_shallowest_compose_per_top_level(
    copy_asset: Callable[[str], Path],
) -> None:
    repo = copy_asset("discovery")

    selection = select_compose_files((str(repo),))

    assert selection.root == repo
    assert selection.files == (repo / "stack" / "compose.yaml",)


def test_missing_glob_crashes_loudly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="matched no files"):
        select_compose_files((str(tmp_path / "missing" / "**" / "compose.yml"),))
