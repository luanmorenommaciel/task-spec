#!/usr/bin/env python3
"""Build a deterministic archive of normalized, credential-free release evidence."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import pathlib
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED = {"checksums.txt", "release-report.json"}


def evidence_paths(version: str) -> list[pathlib.Path]:
    candidates = [
        ROOT / "release" / "evidence.json",
        ROOT / "release" / "quality-rubric.json",
    ]
    for base in (ROOT / "release" / version, ROOT / "interop"):
        if base.exists():
            candidates.extend(path for path in base.rglob("*") if path.is_file())
    result = []
    for path in candidates:
        if "__pycache__" in path.parts or path.name in EXCLUDED:
            continue
        result.append(path)
    return sorted(set(result), key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="dist")
    parser.add_argument("--epoch", type=int, default=None)
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    epoch = args.epoch if args.epoch is not None else int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"task-spec-{version}-evidence.tar.gz"
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w", format=tarfile.PAX_FORMAT) as bundle:
        for source in evidence_paths(version):
            relative = source.relative_to(ROOT)
            content = source.read_bytes()
            info = tarfile.TarInfo(f"task-spec-{version}-evidence/{relative.as_posix()}")
            info.size = len(content)
            info.mtime = epoch
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mode = 0o644
            bundle.addfile(info, io.BytesIO(content))
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            compressed.write(tar_bytes.getvalue())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    print(f"EVIDENCE_ARCHIVE={archive}")
    print(f"EVIDENCE_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
