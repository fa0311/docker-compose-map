from __future__ import annotations

import pytest

from docker_compose_map.domain import GraphName
from docker_compose_map.template import render_with_template


def test_template_without_markers_crashes_loudly() -> None:
    graphs = {graph_name: "graph LR" for graph_name in GraphName}

    with pytest.raises(ValueError, match="compose-map:map:start"):
        render_with_template("plain markdown\n", graphs)
