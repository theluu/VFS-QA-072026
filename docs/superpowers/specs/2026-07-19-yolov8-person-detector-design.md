# Design: Ultralytics YOLOv8 person detector (default for annotation)

**Date:** 2026-07-19
**Status:** Approved (brainstorm), pending implementation plan
**Author:** thel88 + Claude

## Problem

The annotated bbox video the current pipeline produces does not detect small,
distant people as well as the reference sample
(`VIRAT_S_000200_01_000226_000268_person_detected-0001_0.0s-42.0s_bbox.mp4`).
The sample — produced by the sibling `VSF-Project` repo's renderer — reliably
puts tight boxes on tiny parking-lot figures because it runs **Ultralytics
YOLO** (yolov8). QA-Vin's current path runs **OpenCV-DNN YOLOv4**, which was
chosen specifically to avoid Ultralytics' AGPL-3.0 license.

We are reversing that license decision for this POC and adding a YOLOv8 backend
so QA-Vin's annotation output matches the sample's detection quality.

## Decisions (from brainstorm)

- **Scope: swap the detector only.** Keep the entire downstream annotate/bbox
  flow unchanged — `bbox_video.py` / `annotate_video.py` structure, the
  `IouTracker`, `TRACK_COLORS`, the `person #<id> 0.xx` label format, the output
  filename convention, and the ffmpeg encode. We are NOT reproducing the
  sample's header banner or `episode_NNNNNN` label format, and NOT porting
  VSF-Project's renderer.
- **Licensing: accept Ultralytics (AGPL-3.0)** as a dependency for this POC.
- **Default weight: `yolov8m.pt`** (best recall on small/distant people; CPU-only
  on this machine is acceptable).
- **yolov8 becomes the default model** in the annotate CLI/pipeline; `yolov4` and
  `mobilenet-ssd` remain selectable.
- **cv2 conflict resolution:** ~~keep headless~~ **superseded during
  implementation** — ultralytics calls `cv2.imshow` at import time, which the
  headless build lacks, so the project must use the full `opencv-python<5` (still
  has the Caffe importer the fallbacks need). See ADR-007.
- **imgsz = 640** ~~(matches the reference)~~ **corrected to 1920 during
  implementation.** Measured on VIRAT: 640 finds **0** people, 1920 finds them at
  ~0.4-0.7 confidence, matching the sample. 640 was a wrong assumption about the
  reference's settings. Cost: ~2.5s/frame on CPU.
- **Runtime: Python 3.11.** torch has no build for this repo's Python 3.14 (nor
  3.12+ on Intel macOS), so the project venv moves to 3.11. torch 2.2.2 (the last
  Intel-mac build) needs `numpy<2`.

## Non-goals

- No header banner / episode-id overlay (that is VSF-Project's `debug_renderer`
  style; out of scope).
- No change to tracking, label text, colors, output naming, or encode settings.
- No GPU/CUDA support work — CPU inference only on this machine.
- No re-run of the whole mining/triage dataset; this change is about the
  annotation (bbox video) output quality.

## Architecture

Single new unit: a `YoloV8Detector` that implements the existing
`PersonDetector` interface. Because every consumer (`bbox_video.py`, the
tracker, `annotate_video.py`, `triage_person.py`, `eval_person_detector.py`)
already talks to detectors only through `build_detector()` +
`detect_people(frame, min_confidence) -> list[PersonBox]`, the swap is contained
to `detectors.py` plus default-value edits at the call sites.

```
build_detector("yolov8", models_root)
      -> YoloV8Detector(models_root/"yolov8")     # new
      -> YoloV4Detector(...)                        # unchanged
      -> MobileNetSsdDetector(...)                  # unchanged

detector.detect_people(frame, min_confidence) -> list[PersonBox]   # same contract
      -> IouTracker.update(...)                                     # unchanged
      -> draw_tracks(...)  # 'person #<id> 0.xx'                    # unchanged
```

### Component: `YoloV8Detector` (`apps/candidate-mining/src/candidate_mining/detectors.py`)

- **What it does:** person detection with Ultralytics YOLOv8, returning the same
  normalized `PersonBox(x, y, w, h, confidence)` values (coords in 0..1) as the
  other backends.
- **How it is used:** `build_detector("yolov8", models_root)`; then
  `detect_people(frame, min_confidence)`.
- **Dependencies:** `ultralytics` (lazy-imported inside the method/first-use, so
  importing `detectors.py` never pulls torch); the weights file
  `models/yolov8/yolov8m.pt`.

Behavior:
- Constructor stores `model_dir` and weight filename (default `yolov8m.pt`);
  raises `FileNotFoundError` with the same "Run `make fetch-person-model` first"
  message style if the weight is missing. Model object is loaded lazily on first
  `detect_people` call.
- `detect_people(frame, min_confidence)`:
  - `model.predict(frame, classes=[0], conf=min_confidence, iou=0.45,`
    `imgsz=1920, device="cpu", verbose=False)`
  - For each result box: read pixel `xyxy`, normalize by the frame's actual
    width/height, build `PersonBox(x=x1/W, y=y1/H, w=(x2-x1)/W, h=(y2-y1)/H,`
    `confidence=conf)`, clamped to 0..1.
  - Returns `[]` when nothing is found. (Ultralytics already applies NMS, so no
    separate `NMSBoxes` step is needed, unlike the YOLOv4 path.)

Rationale for `class YoloV8Detector` constants: `COCO_PERSON_CLASS_ID = 0`
(already defined in the module), IoU 0.45 mirror the reference; imgsz is 1920 (see above)
`PersonYoloSettings`.

## Call-site changes (default flip)

Change default from `"yolov4"` to `"yolov8"` and add `"yolov8"` to the argparse
`choices` in:

- `apps/candidate-mining/src/candidate_mining/bbox_video.py`
  (`render_person_bbox_video(..., model: str = "yolov8")`)
- `scripts/annotate_video.py` (`--model` default + choices)
- `scripts/triage_person.py` (`--model` default + choices)
- `scripts/eval_person_detector.py` (`--model` default + choices)
- `apps/candidate-mining/src/candidate_mining/person_detect.py` (default in its
  `build_detector` wrapper, if it hard-codes one)
- Register `"yolov8"` in `build_detector()` in `detectors.py`.

`apps/annotation-tool/backend/src/annotation_api/app.py` calls
`render_person_bbox_video` — it inherits the new default automatically; confirm it
does not pass `model="yolov4"` explicitly.

## Weights & fetching

- Move the already-downloaded `yolov8{n,s,m}.pt` from the repo root into
  `models/yolov8/` (per-model convention matching `models/yolov4/`;
  `models/` is gitignored so nothing large is committed).
- Add the three weights to `scripts/fetch_person_model.py` so
  `make fetch-person-model` downloads them from Ultralytics' GitHub release URLs
  (skip-if-exists, like the current entries).

## Dependency & the cv2 conflict

- Add `ultralytics>=8.2` to `pyproject.toml` `[project].dependencies`.
- Ultralytics declares `opencv-python` as a dependency, which would collide with
  the pinned `opencv-python-headless<5` (both provide the `cv2` module).
  Mitigation: install Ultralytics without letting it replace/duplicate opencv
  (e.g. `pip install --no-deps` for the opencv requirement, or install
  ultralytics then reinstall `opencv-python-headless` so headless wins), and
  **verify `python -c "import cv2"` still works** and the annotation server still
  starts. Document the exact install steps taken in the runbook / Makefile.
- Note: Ultralytics also pulls **torch/torchvision** (large, CPU-only here). This
  is an accepted cost of the license/quality decision.

## Docs to correct (avoid contradictory comments)

These currently assert "Ultralytics is avoided because AGPL-3.0"; update them to
record the reversal for this POC:

- `apps/candidate-mining/src/candidate_mining/detectors.py` module docstring.
- `scripts/fetch_person_model.py` module docstring / comments.
- `DECISIONS.md` — add an entry recording that Ultralytics YOLOv8 is now the
  default person detector for annotation, with the AGPL trade-off noted.

## Testing (TDD)

1. **Unit test** (`tests/test_candidate_mining.py` or a new
   `tests/test_yolov8_detector.py`): monkeypatch/mocking so
   `from ultralytics import YOLO` returns a fake model whose `predict` yields a
   result with known pixel `xyxy` boxes + confidences. Assert:
   - coordinates are normalized correctly against a known frame width/height,
   - boxes below `min_confidence` are excluded (or that `conf=` is forwarded),
   - only class 0 is requested,
   - empty result -> `[]`.
   No torch, no weights, no GPU required — runs in CI.
2. **Manual end-to-end verification** (not CI): run `make annotate-video
   INPUT=<VIRAT clip>` with the default yolov8m and visually confirm boxes track
   the small figures the way the sample does.

## Risks

- **cv2 dependency clash** is the main integration risk (mitigation above).
- **CPU inference speed:** yolov8m at imgsz 1920, ~2.5s/frame; a 42s clip at
  5-fps sampling is ~9 min. Slow but acceptable for the POC; the UI's default
  0.5-fps sampling renders in ~1 min.
- torch install size / first-run environment setup friction.
