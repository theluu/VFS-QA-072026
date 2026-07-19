"""Download a labeled evaluation set for the person detector.

The sample corpus in data/raw cannot measure the detector: it contains no real
people, so every "person" hit there is a false positive and there is nothing to
recall. This set pairs public-domain live-action film (real people) with footage
known to have none, so precision and recall are computable.

Labels live in data/eval/person-detection/expected.json and are set by a human
looking at frames - they are the ground truth this repo measures against.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = REPO_ROOT / "data" / "eval" / "person-detection"

# expected_has_person is a placeholder until a human confirms it by viewing
# frames; verify_eval_labels.py rewrites expected.json with confirmed values.
CATALOG: list[dict] = [
    {
        "name": "pd-abolene-cream.mp4",
        "url": "https://archive.org/download/abolene_cream/abolene_cream_512kb.mp4",
        "source": "archive.org, public domain (Prelinger)",
        "note": "1950s advert, live action",
    },
    {
        "name": "pd-sunbeam-commercial.mp4",
        "url": "https://archive.org/download/sunbeam_commercial_6/sunbeam_commercial_6_512kb.mp4",
        "source": "archive.org, public domain (Prelinger)",
        "note": "commercial, live action",
    },
    {
        "name": "pd-duck-and-cover.mp4",
        "url": "https://archive.org/download/DuckandC1951/DuckandC1951_512kb.mp4",
        "source": "archive.org, public domain",
        "note": "1951 civil defence film, children and adults",
    },
    {
        "name": "pd-cep502.mp4",
        "url": "https://archive.org/download/CEP502/CEP502_512kb.mp4",
        "source": "archive.org, public domain (Prelinger)",
        "note": "educational film, live action",
    },
    {
        "name": "pd-when-you-know.mp4",
        "url": "https://archive.org/download/WhenYouK1936/WhenYouK1936_512kb.mp4",
        "source": "archive.org, public domain (Prelinger)",
        "note": "1936 film, live action",
    },
    {
        "name": "pd-victory-1942.mp4",
        "url": "https://archive.org/download/VictoryI1942/VictoryI1942_512kb.mp4",
        "source": "archive.org, public domain (Prelinger)",
        "note": "1942 wartime film, live action",
    },
]

# Known-negative clips already downloaded by fetch_sample_videos.py.
NEGATIVES_FROM_RAW = [
    "ocean.mp4",
    "street-30s.mp4",
    "street-15s.mp4",
    "jellyfish-720p-2mb.mp4",
]


def download(url: str, target: Path, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "vsf-poc-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        target.write_bytes(response.read())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    failures = 0

    for item in CATALOG:
        target = EVAL_DIR / item["name"]
        if target.exists() and not args.force:
            print(f"skip (exists)  {item['name']}")
        else:
            print(f"downloading    {item['name']}")
            try:
                download(item["url"], target, args.timeout)
            except Exception as exc:
                print(f"  FAILED: {exc}", file=sys.stderr)
                failures += 1
                continue
            print(f"  ok  {target.stat().st_size // 1024 // 1024} MB")
        entries.append(
            {
                "video_path": str(target.relative_to(REPO_ROOT)),
                "expected_has_person": None,
                "source": item["source"],
                "note": item["note"],
            }
        )

    raw_dir = REPO_ROOT / "data" / "raw"
    for name in NEGATIVES_FROM_RAW:
        candidate = raw_dir / name
        if not candidate.exists():
            print(f"skip (missing) {name} - run `make fetch-videos` first", file=sys.stderr)
            continue
        entries.append(
            {
                "video_path": str(candidate.relative_to(REPO_ROOT)),
                "expected_has_person": None,
                "source": "data/raw sample corpus",
                "note": "expected negative, confirm by viewing frames",
            }
        )

    expected_path = EVAL_DIR / "expected.json"
    if expected_path.exists() and not args.force:
        existing = json.loads(expected_path.read_text(encoding="utf-8"))
        known = {item["video_path"]: item.get("expected_has_person") for item in existing["videos"]}
        for entry in entries:
            if known.get(entry["video_path"]) is not None:
                entry["expected_has_person"] = known[entry["video_path"]]

    expected_path.write_text(
        json.dumps({"schema_version": "1.0.0", "videos": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {expected_path.relative_to(REPO_ROOT)} with {len(entries)} videos")
    print("expected_has_person is null until a human confirms each label.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
