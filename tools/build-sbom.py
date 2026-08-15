#!/usr/bin/env python3
"""Generate a deterministic SPDX 2.3 SBOM for a Task-Spec release archive."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import pathlib
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha1(value: bytes) -> str:
    return hashlib.sha1(value).hexdigest()  # noqa: S324 - required by SPDX package verification code


def spdx_id(path: str) -> str:
    return "SPDXRef-File-" + sha256(path.encode("utf-8"))[:24]


def created(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--epoch", type=int, default=0)
    args = parser.parse_args()

    archive = pathlib.Path(args.archive).resolve()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    archive_digest = sha256(archive.read_bytes())
    files = []
    verification_hashes = []
    relationships = []
    with tarfile.open(archive, "r:gz") as bundle:
        for member in sorted(bundle.getmembers(), key=lambda item: item.name):
            if not member.isfile():
                continue
            handle = bundle.extractfile(member)
            if handle is None:
                raise ValueError(f"cannot read archive member {member.name}")
            content = handle.read()
            identifier = spdx_id(member.name)
            files.append({
                "SPDXID": identifier,
                "fileName": "./" + member.name,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": sha256(content)},
                    {"algorithm": "SHA1", "checksumValue": sha1(content)},
                ],
                "licenseConcluded": "NOASSERTION",
                "copyrightText": "NOASSERTION",
            })
            verification_hashes.append(sha1(content))
            relationships.append({
                "spdxElementId": "SPDXRef-Package-Task-Spec",
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": identifier,
            })
    verification = sha1("".join(sorted(verification_hashes)).encode("ascii"))
    document = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"task-spec-{version}",
        "documentNamespace": f"https://github.com/luanmorenommaciel/task-spec/releases/tag/v{version}/sbom/{archive_digest}",
        "creationInfo": {
            "created": created(args.epoch),
            "creators": ["Tool: task-spec-build-sbom/1"],
            "licenseListVersion": "3.25",
        },
        "documentDescribes": ["SPDXRef-Package-Task-Spec"],
        "packages": [{
            "name": "task-spec",
            "SPDXID": "SPDXRef-Package-Task-Spec",
            "versionInfo": version,
            "downloadLocation": f"https://github.com/luanmorenommaciel/task-spec/releases/download/v{version}/{archive.name}",
            "filesAnalyzed": True,
            "packageVerificationCode": {"packageVerificationCodeValue": verification},
            "checksums": [{"algorithm": "SHA256", "checksumValue": archive_digest}],
            "licenseConcluded": "MIT",
            "licenseDeclared": "MIT",
            "copyrightText": "NOASSERTION",
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:github/luanmorenommaciel/task-spec@v{version}",
            }],
        }],
        "files": files,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-Task-Spec",
            },
            *relationships,
        ],
    }
    out = pathlib.Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SBOM=READY path={out} files={len(files)} archive_sha256={archive_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
