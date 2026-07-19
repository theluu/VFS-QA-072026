# Changelog

## Unreleased

### Added

- Repository skeleton theo `plan.md`.
- JSON Schema cho candidate manifest, annotation export va coverage report.
- Sample JSON va invalid fixtures.
- Validation scripts va unit tests.
- Candidate mining CLI POC dung ffprobe/ffmpeg.
- FastAPI annotation backend.
- React annotation UI.
- Optional LLM review-note helper voi OpenAI SDK lazy import.
- API integration tests va coverage/release tests.
- Web triage co endpoint tao candidate-mining outputs tu raw video co nguoi detect.
- Candidate-mining helper tao manifest/clips/inventory tu person-detection timestamps.
- Web triage co endpoint va UI tao video MP4 bbox burn-in giong reference VIRAT.

### Changed

- README duoc chuyen thanh quickstart cho POC FastAPI/React.
- Makefile uu tien `.venv/bin/python` sau khi setup va cho phep cau hinh API/frontend port.
- Frontend dependency duoc nang len Vite 8.1.5 de xu ly npm audit vulnerabilities.
- `scripts/mine_from_triage.py` dung chung logic output voi web triage.
- Bbox review video dat ten theo format `{video}_person_detected-0001_0.0s-{duration}s_bbox.mp4`.

### Fixed

- Them `docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md` de khong con link bi hong.

### Removed

- Chua co.
