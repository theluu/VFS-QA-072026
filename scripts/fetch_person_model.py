"""Download the person detector weights into models/.

yolov8 (Ultralytics) is the default detector and gives the best recall on small,
distant people - matching the reference annotated sample. Its weights are
AGPL-3.0; the POC accepts that trade-off (see DECISIONS.md). yolov4 (darknet,
public domain) and MobileNet-SSD remain as permissive-license fallbacks.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_ROOT = REPO_ROOT / "models"

# yolov8 is the default. yolov8m is the rendered default weight; n/s are pulled
# too so a caller can trade accuracy for speed. Weights come from the Ultralytics
# assets release (AGPL-3.0). yolov4/MobileNet-SSD stay as permissive fallbacks.
ULTRALYTICS_RELEASE = "https://github.com/ultralytics/assets/releases/download/v8.2.0"
FILES = [
    (
        "yolov8/yolov8n.pt",
        f"{ULTRALYTICS_RELEASE}/yolov8n.pt",
    ),
    (
        "yolov8/yolov8s.pt",
        f"{ULTRALYTICS_RELEASE}/yolov8s.pt",
    ),
    (
        "yolov8/yolov8m.pt",
        f"{ULTRALYTICS_RELEASE}/yolov8m.pt",
    ),
    (
        "yolov4/yolov4.cfg",
        "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4.cfg",
    ),
    (
        "yolov4/yolov4.weights",
        "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights",
    ),
    (
        "mobilenet-ssd/MobileNetSSD_deploy.prototxt",
        "https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.prototxt",
    ),
    (
        "mobilenet-ssd/MobileNetSSD_deploy.caffemodel",
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

    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    for name, url in FILES:
        target = MODELS_ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
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

    print(f"\nModels ready at {MODELS_ROOT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
