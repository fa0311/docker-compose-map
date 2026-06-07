from __future__ import annotations

from pathlib import Path
from shutil import copytree

from typer.testing import CliRunner

from docker_compose_map.cli import app

runner = CliRunner()
ASSETS = Path(__file__).parent / "assets"


def copy_asset(name: str, tmp_path: Path) -> Path:
    destination = tmp_path / name
    copytree(ASSETS / name, destination)
    return destination


def test_cli_keeps_generated_markdown_output_unchanged(tmp_path: Path) -> None:
    repo = copy_asset("render", tmp_path)
    output = repo / "compose-graph.md"
    expected = (ASSETS / "render" / "compose-graph.md").read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [str(repo / "*" / "compose.yaml"), "-o", str(output), "--direction", "TD"],
    )

    assert result.exit_code == 0, result.output
    assert output.read_text(encoding="utf-8") == expected
