#!/usr/bin/env python3
"""Portable atomic-mkdir lock shared by Python frontmatter mutations."""

from __future__ import annotations

import os
import pathlib
import time


class DirectoryLock:
    def __init__(self, path: pathlib.Path, *, attempts: int = 100, interval: float = 0.05, stale_sec: int = 120) -> None:
        self.path = path
        self.attempts = attempts
        self.interval = interval
        self.stale_sec = stale_sec

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def _reclaim_stale(self) -> None:
        try:
            age = time.time() - self.path.stat().st_mtime
            raw = (self.path / "pid").read_text(encoding="utf-8").strip()
            holder = int(raw) if raw.isdigit() else 0
            if age < self.stale_sec or (holder and self._alive(holder)):
                return
            for name in ("pid", "owner"):
                (self.path / name).unlink(missing_ok=True)
            self.path.rmdir()
        except (OSError, ValueError):
            return

    def __enter__(self) -> "DirectoryLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(self.attempts):
            try:
                self.path.mkdir()
                (self.path / "pid").write_text(str(os.getpid()), encoding="utf-8")
                return self
            except FileExistsError:
                self._reclaim_stale()
                time.sleep(self.interval)
        raise RuntimeError(f"task-state lock is busy: {self.path}")

    def __exit__(self, *_: object) -> None:
        try:
            (self.path / "pid").unlink(missing_ok=True)
            (self.path / "owner").unlink(missing_ok=True)
            self.path.rmdir()
        except OSError:
            pass
