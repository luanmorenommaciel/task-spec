"""The four deterministic, fail-closed TaskSpec decomposition transformations."""

from __future__ import annotations

from decompose.paths import PLAN_DIR

from decompose.engine.compilation import (
    compile_graph,
    derive_task_bundle,
    inspect_lineage,
)
from decompose.engine.graph import render_graph_mermaid
from decompose.engine.planning import accept_plan, build_plan, verify_plan
from decompose.engine.seams import map_recipe, verify_seam_map

__all__ = [
    "accept_plan",
    "build_plan",
    "compile_graph",
    "derive_task_bundle",
    "inspect_lineage",
    "map_recipe",
    "render_graph_mermaid",
    "verify_plan",
    "verify_seam_map",
]
