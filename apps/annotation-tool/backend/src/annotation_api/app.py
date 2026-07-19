from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from scripts.validation_core import REPO_ROOT, write_json

from . import __version__
from .llm import draft_review_note
from .service import (
    export_annotations,
    load_config,
    load_manifest,
    safe_repo_path,
    validate_manifest_payload,
)

app = FastAPI(
    title="AI Camera Annotation API",
    version=__version__,
    description="Local annotation backend for candidate manifest review.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "version": __version__}


@app.get("/config")
def get_config() -> dict[str, Any]:
    return load_config()


@app.get("/manifest")
def get_manifest(
    path: str = Query("data/samples/candidate-manifest.sample.json"),
) -> dict[str, Any]:
    try:
        manifest = load_manifest(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": path, "manifest": manifest}


@app.get("/manifests")
def list_manifests() -> dict[str, Any]:
    """Manifests the UI can open, mined runs first.

    The sample fixture is listed last and only as a fallback: its clips are not
    real files, so opening it first would show an empty player.
    """
    runs_dir = REPO_ROOT / "outputs" / "runs"
    paths = [
        str(candidate.relative_to(REPO_ROOT))
        for candidate in sorted(runs_dir.glob("*/candidate-manifest.json"))
    ]
    sample = REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json"
    if sample.exists():
        paths.append(str(sample.relative_to(REPO_ROOT)))
    return {"manifests": paths}


@app.post("/manifest/validate")
async def validate_manifest(request: Request) -> dict[str, Any]:
    payload = await request.json()
    errors = validate_manifest_payload(payload)
    return {"ok": not errors, "errors": errors}


@app.get("/clips/{clip_path:path}")
def get_clip(clip_path: str) -> FileResponse:
    try:
        path = safe_repo_path(clip_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(path, media_type="video/mp4", filename=Path(path).name)


@app.post("/annotations/export")
async def post_annotation_export(request: Request) -> dict[str, Any]:
    payload = await request.json()
    try:
        result = export_annotations(
            manifest_path=payload["manifest_path"],
            annotation_batch_id=payload["annotation_batch_id"],
            annotations=payload["annotations"],
            output_path=payload.get("output_path"),
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Missing field {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result["ok"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    return result


@app.post("/llm/review-note")
async def post_llm_review_note(request: Request) -> dict[str, Any]:
    payload = await request.json()
    sample = payload.get("sample")
    if not isinstance(sample, dict):
        raise HTTPException(status_code=400, detail="sample object is required")
    annotation = payload.get("annotation")
    if annotation is not None and not isinstance(annotation, dict):
        raise HTTPException(status_code=400, detail="annotation must be an object")
    return draft_review_note(sample, annotation)


@app.get("/repo")
def repo_info() -> dict[str, str]:
    return {"root": REPO_ROOT.name}


# --- Person triage -----------------------------------------------------------
# Detection takes minutes on a long video, far past an HTTP timeout, so /run
# starts a worker thread and the UI polls /status.

_triage_lock = threading.Lock()
_triage_state: dict[str, Any] = {
    "status": "idle",  # idle | running | done | error
    "processed": 0,
    "total": 0,
    "current": "",
    "error": "",
    "report": None,
    "report_path": "",
    "frame_done": 0,
    "frame_total": 0,
    "percent": 0,
}

# Results accumulate across runs, keyed by video path, so re-checking one video
# replaces just that row instead of wiping the results for everything else.
_triage_results: dict[str, Any] = {}


def _set_triage(**fields: Any) -> None:
    with _triage_lock:
        _triage_state.update(fields)


def _run_triage(video_paths: list[str], settings: dict[str, Any]) -> None:
    try:
        from candidate_mining.person_detect import detect_persons_in_video, load_detector

        from scripts.triage_person import build_report

        videos = [REPO_ROOT / path for path in video_paths]
        _set_triage(status="running", processed=0, total=len(videos), error="", report=None)

        net = load_detector(REPO_ROOT / "models", settings.get("model", "yolov4"))
        total_videos = len(videos)

        for index, (video, path) in enumerate(zip(videos, video_paths, strict=True)):
            _set_triage(current=video.name, processed=index)

            def report_frames(done: int, total: int, _index: int = index) -> None:
                # Percent spans the whole run: finished videos plus how far into
                # the current one, so a single long video still moves the bar.
                fraction = (done / total) if total else 0
                _set_triage(
                    frame_done=done,
                    frame_total=total,
                    percent=round((_index + fraction) / total_videos * 100),
                )

            result = detect_persons_in_video(
                video,
                net,
                sample_interval_ms=settings["sample_interval_ms"],
                min_confidence=settings["min_confidence"],
                min_hits=settings["min_hits"],
                on_progress=report_frames,
            )
            with _triage_lock:
                _triage_results[path] = result

        with _triage_lock:
            accumulated = list(_triage_results.values())
        report = build_report(accumulated, settings, detector_name=settings.get("model", "yolov4"))
        report_path = REPO_ROOT / "outputs" / "reports" / "triage-web.json"
        write_json(report_path, report)
        _set_triage(
            status="done",
            processed=len(videos),
            current="",
            report=report,
            report_path=str(report_path.relative_to(REPO_ROOT)),
            percent=100,
        )
    except Exception as exc:
        _set_triage(status="error", error=str(exc), current="")


@app.get("/triage/status")
def triage_status() -> dict[str, Any]:
    with _triage_lock:
        return dict(_triage_state)


@app.post("/triage/run")
async def triage_run(request: Request) -> dict[str, Any]:
    with _triage_lock:
        if _triage_state["status"] == "running":
            raise HTTPException(status_code=409, detail="A triage run is already in progress")

    payload = await request.json()
    requested = payload.get("videos")

    if requested:
        video_paths = []
        for path in requested:
            try:
                resolved = safe_repo_path(path)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if not resolved.is_file():
                raise HTTPException(status_code=400, detail=f"Not a file: {path}")
            video_paths.append(path)
    else:
        input_dir = payload.get("input", "data/raw")
        try:
            safe_repo_path(input_dir)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        from scripts.triage_person import collect_videos

        video_paths = [str(p.relative_to(REPO_ROOT)) for p in collect_videos(input_dir)]

    if not video_paths:
        raise HTTPException(status_code=400, detail="No videos selected")

    settings = {
        "sample_interval_ms": int(payload.get("sample_interval_ms", 1000)),
        "min_confidence": float(payload.get("min_confidence", 0.5)),
        "min_hits": int(payload.get("min_hits", 2)),
        "model": payload.get("model", "yolov4"),
    }

    _set_triage(
        status="running",
        processed=0,
        total=len(video_paths),
        current="",
        error="",
        report=None,
        report_path="",
        frame_done=0,
        frame_total=0,
        percent=0,
    )
    threading.Thread(target=_run_triage, args=(video_paths, settings), daemon=True).start()
    return {"started": True, "count": len(video_paths), "settings": settings}


@app.post("/triage/mine")
async def triage_mine(request: Request) -> dict[str, Any]:
    with _triage_lock:
        if _triage_state["status"] == "running":
            raise HTTPException(status_code=409, detail="A triage run is still in progress")
        report = _triage_state.get("report")

    if not isinstance(report, dict):
        raise HTTPException(status_code=400, detail="Run person detection before mining candidates")

    payload = await request.json()
    requested = payload.get("videos") or report.get("kept") or []
    if not isinstance(requested, list) or not requested:
        raise HTTPException(status_code=400, detail="No videos selected for candidate mining")

    output_root_raw = str(payload.get("output_root") or "outputs/runs")
    try:
        output_root = safe_repo_path(output_root_raw)
        output_root.relative_to(REPO_ROOT / "outputs")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Output root must be under outputs/: {exc}") from exc

    try:
        random_seed = int(payload.get("random_seed", 42))
        merge_gap_ms = int(payload.get("merge_gap_ms", 3000))
        padding_ms = int(payload.get("padding_ms", load_config().get("clip_padding_ms", 30000)))
        max_clips_per_video = int(payload.get("max_clips_per_video", 6))
        background_count = int(payload.get("background_count", 2))
        background_duration_ms = int(payload.get("background_duration_ms", 15000))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid mining setting: {exc}") from exc

    from candidate_mining.detected import mine_person_detection_video, safe_run_id

    videos = report.get("videos") or []
    kept_entries = {
        item["video_path"]: item
        for item in videos
        if isinstance(item, dict) and item.get("decision") == "keep" and item.get("video_path")
    }
    outputs = []
    errors = []
    for video_path in requested:
        if video_path not in kept_entries:
            errors.append(f"No kept person-detection result for {video_path}")
            continue
        try:
            source = safe_repo_path(str(video_path))
            if not source.is_file():
                raise FileNotFoundError(f"Not a file: {video_path}")
            entry = {
                **kept_entries[video_path],
                "detector": report.get("detector", "unknown"),
                "settings": report.get("settings", {}),
            }
            result = mine_person_detection_video(
                video_path=source,
                detection_entry=entry,
                output_dir=output_root / safe_run_id(source),
                dataset_id=str(payload.get("dataset_id") or "person-detected"),
                random_seed=random_seed,
                merge_gap_ms=merge_gap_ms,
                padding_ms=padding_ms,
                max_clips_per_video=max_clips_per_video,
                background_count=background_count,
                background_duration_ms=background_duration_ms,
                project_root=REPO_ROOT,
            )
            outputs.append(result)
        except Exception as exc:
            errors.append(f"{video_path}: {exc}")

    if not outputs:
        raise HTTPException(status_code=422, detail=errors or ["No candidate output was generated"])
    return {"ok": not errors, "outputs": outputs, "errors": errors}


@app.post("/triage/bbox")
async def triage_bbox(request: Request) -> dict[str, Any]:
    payload = await request.json()
    video_path = payload.get("path")
    if not isinstance(video_path, str) or not video_path:
        raise HTTPException(status_code=400, detail="path is required")
    try:
        source = safe_repo_path(video_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not source.is_file():
        raise HTTPException(status_code=400, detail=f"Not a file: {video_path}")

    try:
        model = str(payload.get("model") or "yolov8")
        sample_fps = float(payload.get("sample_fps", 0.5))
        min_confidence = float(payload.get("min_confidence", 0.3))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid bbox setting: {exc}") from exc

    from candidate_mining.bbox_video import render_person_bbox_video

    try:
        result = await run_in_threadpool(
            render_person_bbox_video,
            input_path=source,
            models_root=REPO_ROOT / "models",
            model=model,
            sample_fps=sample_fps,
            min_confidence=min_confidence,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cannot render bbox video: {exc}") from exc
    return {"ok": True, "result": result}


ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi"}


@app.post("/triage/upload")
async def triage_upload(
    file: UploadFile = File(...),
    path: str = Form("data/raw"),
) -> dict[str, Any]:
    """Add a video to an input folder from the UI."""
    try:
        directory = safe_repo_path(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")

    # Strip any directory component: a filename is not a path, and an uploaded
    # "../../x.mp4" must not escape the target folder.
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if not filename or suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(sorted(ALLOWED_VIDEO_SUFFIXES))} are accepted",
        )

    target = directory / filename
    stem = Path(filename).stem
    counter = 1
    while target.exists():
        target = directory / f"{stem}-{counter}{suffix}"
        counter += 1

    size = 0
    try:
        with target.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                handle.write(chunk)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Cannot save file: {exc}") from exc

    # A file the detector cannot open is worse than no file: reject it now
    # rather than failing mid-run.
    try:
        from candidate_mining.video import probe_video

        probe = probe_video(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Not a readable video: {exc}") from exc

    return {
        "path": str(target.relative_to(REPO_ROOT)),
        "name": target.name,
        "size_mb": round(size / 1024 / 1024, 1),
        "duration_ms": probe["duration_ms"],
    }


_proxy_lock = threading.Lock()


@app.get("/triage/preview")
def triage_preview(path: str = Query(...)) -> FileResponse:
    """Serve a video the browser can actually play.

    Surveillance footage is often MPEG-4 Part 2 or MJPEG, which Chrome refuses.
    Those get an H.264 proxy, built once and cached; the original is untouched
    and stays what the detector reads.
    """
    from candidate_mining.video import BROWSER_SAFE_CODECS, probe_video, transcode_for_web

    try:
        source = safe_repo_path(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        probe = probe_video(source)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot read video: {exc}") from exc

    if probe["codec_name"] in BROWSER_SAFE_CODECS:
        return FileResponse(source, media_type="video/mp4", filename=source.name)

    digest = hashlib.sha256(str(source).encode()).hexdigest()[:12]
    proxy = REPO_ROOT / "outputs" / "proxies" / f"{source.stem}-{digest}.mp4"

    with _proxy_lock:
        if not proxy.exists():
            try:
                transcode_for_web(source, proxy)
            except Exception as exc:
                proxy.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=500, detail=f"Cannot build preview: {exc}"
                ) from exc

    return FileResponse(proxy, media_type="video/mp4", filename=proxy.name)


@app.get("/triage/videos")
def triage_videos(path: str = Query("data/raw")) -> dict[str, Any]:
    """The raw video list, so the UI can show and preview them before any run."""
    try:
        directory = safe_repo_path(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")

    videos = []
    for item in sorted(directory.iterdir()):
        if item.suffix.lower() not in {".mp4", ".mov", ".mkv", ".avi"}:
            continue
        videos.append(
            {
                "path": str(item.relative_to(REPO_ROOT)),
                "name": item.name,
                "size_mb": round(item.stat().st_size / 1024 / 1024, 1),
            }
        )
    return {"path": path, "videos": videos}


@app.get("/triage/inputs")
def triage_inputs() -> dict[str, Any]:
    """Folders that hold videos, so the UI can offer them instead of free text."""
    candidates = []
    for base in (REPO_ROOT / "data" / "raw", REPO_ROOT / "data" / "eval" / "person-detection"):
        if base.is_dir() and any(p.suffix.lower() == ".mp4" for p in base.iterdir()):
            count = sum(1 for p in base.iterdir() if p.suffix.lower() == ".mp4")
            candidates.append({"path": str(base.relative_to(REPO_ROOT)), "video_count": count})
    return {"inputs": candidates}


# Mounted last so every API route above wins the match; StaticFiles only
# receives paths that no API route claimed.
FRONTEND_DIST = REPO_ROOT / "apps" / "annotation-tool" / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
