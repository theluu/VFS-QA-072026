from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from scripts.validation_core import REPO_ROOT

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


# Mounted last so every API route above wins the match; StaticFiles only
# receives paths that no API route claimed.
FRONTEND_DIST = REPO_ROOT / "apps" / "annotation-tool" / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
