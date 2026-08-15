#!/usr/bin/env python3
"""Frozen discriminating tests for the M benchmark."""

from __future__ import annotations

from task_graph import assert_acyclic, ready


diamond = {
    "A": {"status": "done", "depends_on": []},
    "B": {"status": "done", "depends_on": ["A"]},
    "C": {"status": "pending", "depends_on": ["A"]},
    "D": {"status": "pending", "depends_on": ["B", "C"]},
    "E": {"status": "pending", "depends_on": []},
}
assert ready(diamond) == ["C", "E"]
blocked = dict(diamond)
blocked["A"] = {"status": "blocked", "depends_on": []}
assert ready(blocked) == ["E"]

cycle = {
    "alpha": {"status": "pending", "depends_on": ["beta"]},
    "beta": {"status": "pending", "depends_on": ["gamma"]},
    "gamma": {"status": "pending", "depends_on": ["alpha"]},
}
try:
    assert_acyclic(cycle)
except ValueError as exc:
    assert str(exc) in {
        "cycle: alpha -> beta -> gamma -> alpha",
        "cycle: alpha -> gamma -> beta -> alpha",
        "cycle: beta -> alpha -> gamma -> beta",
        "cycle: beta -> gamma -> alpha -> beta",
        "cycle: gamma -> alpha -> beta -> gamma",
        "cycle: gamma -> beta -> alpha -> gamma",
    }, str(exc)
else:
    raise AssertionError("expected named cycle")

print("TASK_GRAPH=READY")
