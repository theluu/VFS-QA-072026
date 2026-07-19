# Annotation Tool

FastAPI backend va React UI de human reviewer gan nhan candidate clips.

## Backend

```bash
make annotation-api
```

API chinh:

- `GET /health`
- `GET /config`
- `GET /manifest?path=data/samples/candidate-manifest.sample.json`
- `POST /manifest/validate`
- `POST /annotations/export`
- `POST /llm/review-note`
- `POST /triage/run`
- `GET /triage/status`
- `POST /triage/mine`
- `POST /triage/bbox`
- `GET /triage/preview?path=data/raw/sample.mp4`

## Frontend

```bash
make annotation-tool
```

## Features

- Load manifest tu duong dan relative.
- Validate manifest khi load.
- Hien thi clip neu clip ton tai.
- Previous/next sample.
- Form gan nhan, timestamp, status, reviewer va comment.
- Auto-save vao `localStorage`.
- Export annotation JSON qua backend.
- Loc raw video bang person detector.
- Tao candidate-mining outputs tu video co nguoi detect va load manifest de gan nhan.
- Tao MP4 bbox burn-in tu raw video de review giong video reference.

## Keyboard Shortcuts

- `ArrowLeft`: previous sample.
- `ArrowRight`: next sample.
- `Ctrl+S` / `Cmd+S`: save current annotation locally.

## Storage

- Progress tam thoi nam trong browser `localStorage`.
- Export chinh thuc ghi vao `outputs/annotations/`.
- Triage report web ghi vao `outputs/reports/triage-web.json`.
- Candidate outputs tu triage ghi vao `outputs/runs/{run_id}/`.
- Video bbox burn-in ghi vao `outputs/annotated/`.
