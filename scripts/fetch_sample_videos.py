"""Download public sample videos into data/raw and generate candidate events.

Videos are not committed; this script rebuilds the local test corpus on demand.
Each entry records its source and license so the dataset card stays traceable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.video import probe_video

REPO_ROOT = Path(__file__).resolve().parents[1]

# Live-action footage from keyless public hosts. These are generic outdoor and
# street scenes, not perimeter CCTV: they exercise the mining pipeline end to
# end, they are not a substitute for representative security footage.
CATALOG: list[dict[str, str]] = [
    {
        "name": "street-5s.mp4",
        "url": "https://download.samplelib.com/mp4/sample-5s.mp4",
        "license": "samplelib free sample",
        "scene": "live-action outdoor",
    },
    {
        "name": "street-10s.mp4",
        "url": "https://download.samplelib.com/mp4/sample-10s.mp4",
        "license": "samplelib free sample",
        "scene": "live-action outdoor",
    },
    {
        "name": "street-15s.mp4",
        "url": "https://download.samplelib.com/mp4/sample-15s.mp4",
        "license": "samplelib free sample",
        "scene": "live-action outdoor",
    },
    {
        "name": "street-20s.mp4",
        "url": "https://download.samplelib.com/mp4/sample-20s.mp4",
        "license": "samplelib free sample",
        "scene": "live-action outdoor",
    },
    {
        "name": "street-30s.mp4",
        "url": "https://download.samplelib.com/mp4/sample-30s.mp4",
        "license": "samplelib free sample",
        "scene": "live-action outdoor",
    },
    {
        "name": "sintel-trailer.mp4",
        "url": "https://media.w3.org/2010/05/sintel/trailer.mp4",
        "license": "CC-BY 3.0 (Blender Foundation)",
        "scene": "animation, cut-heavy",
    },
]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "vsf-poc-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        target.write_bytes(response.read())


def events_for(duration_ms: int) -> dict[str, Any]:
    """Place one candidate window across the middle 40%-60% of the video."""
    start_ms = int(duration_ms * 0.4)
    end_ms = int(duration_ms * 0.6)
    return {
        "events": [
            {
                "candidate_rule": "intrusion_manual_v1",
                "candidate_start_ms": start_ms,
                "candidate_end_ms": end_ms,
                "metadata": {
                    "source": "fetch_sample_videos",
                    "note": "Synthetic mid-video window for pipeline testing",
                },
            }
        ]
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/raw", help="Directory for downloaded videos.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--force", action="store_true", help="Re-download existing files.")
    args = parser.parse_args(argv)

    output_dir = REPO_ROOT / args.output
    events_dir = output_dir / "events"
    output_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    failures = 0

    for item in CATALOG:
        target = output_dir / item["name"]
        if target.exists() and not args.force:
            print(f"skip (exists)  {item['name']}")
        else:
            print(f"downloading    {item['name']} <- {item['url']}")
            try:
                download(item["url"], target, args.timeout)
            except Exception as exc:
                print(f"  FAILED: {exc}", file=sys.stderr)
                failures += 1
                continue

        try:
            probe = probe_video(target)
        except Exception as exc:
            print(f"  FAILED to probe {item['name']}: {exc}", file=sys.stderr)
            failures += 1
            continue

        events_path = events_dir / f"{target.stem}.events.json"
        events_path.write_text(
            json.dumps(events_for(probe["duration_ms"]), indent=2) + "\n", encoding="utf-8"
        )

        entries.append(
            {
                "name": item["name"],
                "video_path": str(target.relative_to(REPO_ROOT)),
                "events_path": str(events_path.relative_to(REPO_ROOT)),
                "url": item["url"],
                "license": item["license"],
                "scene": item["scene"],
                "duration_ms": probe["duration_ms"],
                "width": probe["width"],
                "height": probe["height"],
                "codec_name": probe["codec_name"],
                "file_size": probe["file_size"],
                "sha256": sha256_of(target),
            }
        )
        print(f"  ok  {probe['duration_ms']} ms  {probe['width']}x{probe['height']}")

    catalog_path = output_dir / "catalog.json"
    catalog_path.write_text(json.dumps({"videos": entries}, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {catalog_path.relative_to(REPO_ROOT)} with {len(entries)} videos")

    if failures:
        print(f"{failures} video(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
