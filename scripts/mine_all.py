"""Run candidate mining over every video in data/raw/catalog.json.

Window parameters are scaled to each video's duration: the CLI defaults assume
hours-long footage and would swallow these short samples whole.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = ":".join(
    [
        str(REPO_ROOT / "apps" / "candidate-mining" / "src"),
        str(REPO_ROOT / "apps" / "annotation-tool" / "backend" / "src"),
        str(REPO_ROOT),
        str(REPO_ROOT / "scripts"),
    ]
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="data/raw/catalog.json")
    parser.add_argument("--output-root", default="outputs/runs")
    parser.add_argument("--random-seed", type=int, default=42)
    args = parser.parse_args(argv)

    catalog_path = REPO_ROOT / args.catalog
    if not catalog_path.exists():
        print(f"Catalog not found: {args.catalog}. Run `make fetch-videos` first.", file=sys.stderr)
        return 1

    videos = json.loads(catalog_path.read_text(encoding="utf-8"))["videos"]
    env_python = sys.executable
    failures = 0
    run_ids: list[str] = []

    for video in videos:
        duration_ms = video["duration_ms"]
        run_id = Path(video["name"]).stem
        output_dir = REPO_ROOT / args.output_root / run_id
        command = [
            env_python,
            "-m",
            "candidate_mining.cli",
            "--input",
            video["video_path"],
            "--events",
            video["events_path"],
            "--output",
            str(output_dir),
            "--random-seed",
            str(args.random_seed),
            "--padding-ms",
            str(int(duration_ms * 0.05)),
            "--background-duration-ms",
            str(int(duration_ms * 0.10)),
        ]
        print(f"\n=== {run_id} ({duration_ms} ms) ===")
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env={"PYTHONPATH": PYTHONPATH, "PATH": __import__("os").environ["PATH"]},
        )
        if result.returncode != 0:
            failures += 1
            continue
        run_ids.append(run_id)

    print(f"\n{len(run_ids)} run(s) ok, {failures} failed")
    for run_id in run_ids:
        print(f"  outputs/runs/{run_id}/candidate-manifest.json")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
