#!/usr/bin/env python3
"""Build a disposable browser preview and render every README Mermaid block."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


CSS = """
:root { color-scheme: dark; --bg:#091017; --panel:#111c25; --text:#e9f0f5; --muted:#a8b6c2; --line:#2a3a46; --accent:#68c7ff; }
* { box-sizing: border-box; }
html { background: var(--bg); }
body { max-width: 1120px; margin: 0 auto; padding: 32px 40px 80px; background: var(--bg); color: var(--text); font: 16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; overflow-wrap: anywhere; }
h1 { font-size: clamp(2.4rem,7vw,5rem); line-height: 1; margin: 1.2rem 0 .5rem; }
h2 { margin-top: 3.6rem; padding-bottom: .45rem; border-bottom: 1px solid var(--line); font-size: clamp(1.65rem,4vw,2.35rem); }
h3 { margin-top: 2.2rem; }
a { color: var(--accent); }
p { color: var(--muted); }
strong, code { color: var(--text); }
img { display: block; max-width: 100%; height: auto; margin: 24px auto; }
table { display: block; width: 100%; overflow-x: auto; border-collapse: collapse; margin: 20px 0; }
th, td { min-width: 150px; padding: 10px 12px; border: 1px solid var(--line); text-align: left; vertical-align: top; }
th { background: var(--panel); }
pre { overflow-x: auto; padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: #070c11; }
code { font-family: ui-monospace,SFMono-Regular,Menlo,monospace; }
details { padding: 8px 0; border-bottom: 1px solid var(--line); }
@media (max-width: 640px) { body { padding: 18px 16px 56px; font-size: 15px; } h2 { margin-top: 2.8rem; } th,td { min-width: 132px; } }
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--mermaid-version", default="11.9.0")
    args = parser.parse_args()
    out = pathlib.Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"^```mermaid\n(.*?)^```", text, re.M | re.S)
    if not blocks:
        print("README_PREVIEW=INVALID no Mermaid blocks", file=sys.stderr)
        return 1
    for index, source in enumerate(blocks, 1):
        input_path, output_path = out / f"diagram-{index}.mmd", out / f"diagram-{index}.svg"
        input_path.write_text(source, encoding="utf-8")
        completed = subprocess.run([
            "npx", "--yes", f"@mermaid-js/mermaid-cli@{args.mermaid_version}",
            "-i", str(input_path), "-o", str(output_path), "-t", "dark", "-b", "transparent",
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode:
            print(completed.stdout + completed.stderr, file=sys.stderr)
            return completed.returncode
        text = text.replace(f"```mermaid\n{source}```", f"![Rendered Mermaid diagram {index}](diagram-{index}.svg)", 1)
    assets = out / "assets" / "readme"
    if assets.exists():
        shutil.rmtree(assets)
    shutil.copytree(ROOT / "assets" / "readme", assets)
    (out / "README.preview.md").write_text(text, encoding="utf-8")
    (out / "readme.css").write_text(CSS, encoding="utf-8")
    completed = subprocess.run([
        "pandoc", "--from=gfm", "--to=html5", "--standalone", "--metadata", "title=Task-Spec README preview",
        "--css=readme.css", "README.preview.md", "-o", "index.html",
    ], cwd=out, text=True, capture_output=True, check=False)
    if completed.returncode:
        print(completed.stdout + completed.stderr, file=sys.stderr)
        return completed.returncode
    print(f"README_PREVIEW=READY mermaid={len(blocks)} html={out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
