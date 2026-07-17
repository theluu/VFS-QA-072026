"""Download the MobileNet-SSD person detector into models/.

MobileNet-SSD is used instead of YOLO because its weights carry a permissive
license; ultralytics YOLO is AGPL-3.0 and would impose source obligations on a
commercial deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "models" / "mobilenet-ssd"

FILES = [
    (
        "MobileNetSSD_deploy.prototxt",
        "https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.prototxt",
    ),
    (
        "MobileNetSSD_deploy.caffemodel",
        "https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.caffemodel",
    ),
]


def download(url: str, target: Path, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "vsf-poc-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        target.write_bytes(response.read())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FILES:
        target = MODEL_DIR / name
        if target.exists() and not args.force:
            print(f"skip (exists)  {name}  {target.stat().st_size // 1024} KB")
            continue
        print(f"downloading    {name}")
        try:
            download(url, target, args.timeout)
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            return 1
        digest = hashlib.sha256(target.read_bytes()).hexdigest()[:16]
        print(f"  ok  {target.stat().st_size // 1024} KB  sha256:{digest}")

    print(f"\nModel ready at {MODEL_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
