from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from docker_compose_map.cli import app

runner = CliRunner()


def test_cli_keeps_generated_markdown_output_unchanged(
    copy_asset: Callable[[str], Path],
    assets: Path,
) -> None:
    repo = copy_asset("render")
    output = repo / "compose-graph.md"
    expected = (assets / "render" / "compose-graph.md").read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [str(repo / "*" / "compose.yaml"), "-o", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert output.read_text(encoding="utf-8") == expected
