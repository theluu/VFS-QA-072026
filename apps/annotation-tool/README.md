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

## Keyboard Shortcuts

- `ArrowLeft`: previous sample.
- `ArrowRight`: next sample.
- `Ctrl+S` / `Cmd+S`: save current annotation locally.

## Storage

- Progress tam thoi nam trong browser `localStorage`.
- Export chinh thuc ghi vao `outputs/annotations/`.
