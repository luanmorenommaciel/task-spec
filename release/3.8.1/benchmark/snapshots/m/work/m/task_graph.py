#!/usr/bin/env python3
"""Intentionally defective graph helpers for the frozen benchmark."""

from __future__ import annotations


def ready(tasks: dict[str, dict]) -> list[str]:
    return sorted(task_id for task_id, task in tasks.items() if task["status"] == "pending")


def assert_acyclic(tasks: dict[str, dict]) -> None:
    if any(task_id in task.get("depends_on", []) for task_id, task in tasks.items()):
        raise ValueError("cycle")
