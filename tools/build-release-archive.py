#!/usr/bin/env python3
"""Build a deterministic, checksum-backed Task-Spec release archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import pathlib
import stat
import subprocess
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED_ROOTS = {".git", ".taskspec", ".playwright-cli", "dist", "output", "tasks"}


def paths(include_worktree: bool) -> list[pathlib.Path]:
    command = ["git", "ls-files", "-z"]
    if include_worktree:
        command = ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    raw = subprocess.check_output(command, cwd=ROOT)
    return sorted((ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="dist")
    parser.add_argument("--include-worktree", action="store_true", help="include non-ignored untracked files for local packaging tests")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    out_dir = pathlib.Path(args.out_dir).resolve(); out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"task-spec-{version}.tar.gz"
    prefix = f"task-spec-{version}"
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w", format=tarfile.PAX_FORMAT) as bundle:
        for source in paths(args.include_worktree):
            rel = source.relative_to(ROOT)
            if rel.parts[0] in EXCLUDED_ROOTS or "__pycache__" in rel.parts:
                continue
            if rel.parts[0] == "release" and (len(rel.parts) < 2 or rel.parts[1] != "mesh"):
                continue
            arcname = f"{prefix}/{rel.as_posix()}"
            st = source.lstat()
            info = tarfile.TarInfo(arcname); info.mtime = epoch; info.uid = info.gid = 0; info.uname = info.gname = "root"
            if source.is_symlink():
                info.type = tarfile.SYMTYPE; info.linkname = os.readlink(source); info.mode = 0o777
                bundle.addfile(info)
            elif source.is_file():
                data = source.read_bytes(); info.size = len(data)
                info.mode = 0o755 if st.st_mode & stat.S_IXUSR else 0o644
                bundle.addfile(info, io.BytesIO(data))
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            compressed.write(tar_bytes.getvalue())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(archive.name + ".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"RELEASE_ARCHIVE={archive}")
    print(f"RELEASE_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
