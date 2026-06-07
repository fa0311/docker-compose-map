from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from docker_compose_map.domain import GraphName

DEFAULT_TEMPLATE = """# Docker Compose dependency map

## Compose dependencies

<!-- compose-map:dependencies:start -->
<!-- compose-map:dependencies:end -->

## Map

<!-- compose-map:map:start -->
<!-- compose-map:map:end -->

## Network / ports

<!-- compose-map:network:start -->
<!-- compose-map:network:end -->

## Volumes / mounts

<!-- compose-map:volumes:start -->
<!-- compose-map:volumes:end -->
"""


def render_with_template(template: str, graphs: Mapping[GraphName, str]) -> str:
    rendered = template
    for graph_name in GraphName:
        rendered = _replace_graph(rendered, graph_name, graphs[graph_name])
    return rendered


def _replace_graph(template: str, graph_name: GraphName, generated_mermaid: str) -> str:
    start_marker = _start_marker(graph_name)
    end_marker = _end_marker(graph_name)
    if template.count(start_marker) != 1 or template.count(end_marker) != 1:
        return template

    before, after_start = template.split(start_marker, 1)
    if end_marker not in after_start:
        return template
    _, after = after_start.split(end_marker, 1)
    mermaid_block = f"```mermaid\n{generated_mermaid.rstrip()}\n```"
    return f"{before}{start_marker}\n{mermaid_block}\n{end_marker}{after}"


def read_template(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE


def write_graph_template(output_path: Path, graphs: Mapping[GraphName, str]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_with_template(read_template(output_path), graphs),
        encoding="utf-8",
    )
    return output_path


def render_stdout(graphs: Mapping[GraphName, str]) -> str:
    return render_with_template(DEFAULT_TEMPLATE, graphs)


def _start_marker(graph_name: GraphName) -> str:
    return f"<!-- compose-map:{graph_name.value}:start -->"


def _end_marker(graph_name: GraphName) -> str:
    return f"<!-- compose-map:{graph_name.value}:end -->"
