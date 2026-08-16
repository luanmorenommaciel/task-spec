#!/usr/bin/env python3
"""Build deterministic TaskMesh helpers for the supported private-release matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = (("darwin", "amd64"), ("darwin", "arm64"), ("linux", "amd64"), ("linux", "arm64"))


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--target", action="append", help="limit builds to os/arch; repeatable")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    out_dir = pathlib.Path(args.out_dir or f"release/{version}/bin").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    requested = set(args.target or ())
    targets = [target for target in TARGETS if not requested or "/".join(target) in requested]
    if requested - {"/".join(target) for target in targets}:
        raise SystemExit("unsupported TaskMesh target: " + ", ".join(sorted(requested)))
    artifacts = []
    for operating_system, architecture in targets:
        name = f"taskspec-meshd-{operating_system}-{architecture}"
        path = out_dir / name
        environment = dict(os.environ, CGO_ENABLED="0", GOOS=operating_system, GOARCH=architecture)
        subprocess.run(
            ["go", "build", "-buildvcs=false", "-trimpath", "-ldflags=-s -w", "-o", str(path), "./cmd/taskspec-meshd"],
            cwd=ROOT,
            env=environment,
            check=True,
        )
        path.chmod(0o755)
        sha = digest(path)
        (out_dir / f"{name}.sha256").write_text(f"{sha}  {name}\n", encoding="utf-8")
        artifacts.append({"name": name, "os": operating_system, "arch": architecture, "sha256": sha, "size": path.stat().st_size})
    manifest = {
        "contract": "TaskMeshBinaryManifest/v1",
        "version": version,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "go_version": subprocess.check_output(["go", "version"], text=True).strip(),
        "artifacts": artifacts,
    }
    manifest_path = out_dir / "taskmesh-binaries.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    checksums = "".join(f"{row['sha256']}  {row['name']}\n" for row in artifacts)
    (out_dir / "taskmesh-checksums.txt").write_text(checksums, encoding="utf-8")
    print(f"MESH_BINARIES=READY targets={len(artifacts)} manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
