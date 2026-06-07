from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from docker_compose_map.compose import load_stacks
from docker_compose_map.discovery import select_compose_files
from docker_compose_map.domain import Direction
from docker_compose_map.mermaid import render_graphs
from docker_compose_map.template import render_stdout, write_graph_template

app = typer.Typer(add_completion=False, no_args_is_help=False, pretty_exceptions_enable=False)


@app.command()
def main(
    inputs: Annotated[
        list[str],
        typer.Argument(help="Compose file, directory, or glob-like path. Repeat freely."),
    ],
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Markdown template file to update.",
        ),
    ] = None,
    direction: Annotated[
        Direction,
        typer.Option("--direction", "-d", case_sensitive=False, help="Mermaid graph direction."),
    ] = Direction.LR,
) -> None:
    selection = select_compose_files(tuple(inputs))
    stacks = load_stacks(selection)
    graphs = render_graphs(stacks, direction)

    if output is None:
        sys.stdout.write(render_stdout(graphs))
        return

    written = write_graph_template(Path(output), graphs)
    typer.echo(f"wrote {written} ({len(stacks)} stacks)", err=True)


def run() -> None:
    app()
