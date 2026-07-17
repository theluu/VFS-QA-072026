# VSF Project - AI Camera Candidate Mining & Annotation POC

Repository nay ho tro quy trinh chuan bi du lieu test va ground truth cho AI Camera an ninh vanh dai. Model AI da co san va nam ngoai pham vi repository; muc tieu la tao candidate review queue, annotation tool, manifest va artifact ban giao co the truy vet.

## Workflow

```text
B: Raw video -> inventory -> candidate mining -> proxy clips -> candidate manifest
C: candidate manifest -> human review -> annotation export
A/B: annotation export -> validation -> coverage report -> release package
```

## Structure

```text
apps/candidate-mining      Python CLI for video inventory, clips and manifest
apps/annotation-tool       FastAPI backend and React annotation UI
shared/schemas             JSON Schema contracts
configs                    Labels, statuses and local processing config
scripts                    Validation, coverage and release scripts
tests                      Unit and contract tests
data/raw                   Raw videos, not committed
data/samples               Small sample JSON fixtures
outputs                    Generated artifacts, not committed
docs                       Business, contract and runbook docs
```

## Environment

- Python 3.11+
- Node.js 20+
- npm
- ffmpeg and ffprobe for real video processing

## Setup

```bash
make setup
```

Neu chi muon chay validation/test khong can server, dependency ngoai FastAPI/React khong bat buoc vi test hien tai dung standard library.

## OpenAI Key

Dien key local vao `.env`:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_here
```

`.env` khong duoc commit. File mau co san tai `.env.example`.

## Candidate Mining

```bash
make candidate-mining INPUT=data/raw/sample.mp4 EVENTS=data/samples/candidate-events.sample.json RUN_ID=demo
```

Output chinh:

- `outputs/runs/demo/inventory.json`
- `outputs/runs/demo/candidate-manifest.json`
- `outputs/runs/demo/clips/`
- `outputs/runs/demo/run-summary.json`

## Annotation Tool

Backend:

```bash
make annotation-api
```

Frontend:

```bash
make annotation-tool
```

Mac dinh UI goi API tai `http://127.0.0.1:8000`. Neu port 8000 dang ban, chay:

```bash
make annotation-api API_PORT=8020
make annotation-tool API_PORT=8020 API_BASE=http://127.0.0.1:8020 FRONTEND_PORT=5175
```

Trong lan setup hien tai, backend dang chay tai `http://127.0.0.1:8020` va frontend tai `http://127.0.0.1:5175`.

## Validation

```bash
make lint
make test
make validate-schemas
make validate-samples
make validate-dataset MANIFEST=data/samples/candidate-manifest.sample.json ANNOTATIONS=data/samples/annotation-export.sample.json
make coverage-report
npm audit --prefix apps/annotation-tool/frontend
```

## LLM Helper Boundary

Backend co optional endpoint tao review note bang OpenAI SDK neu `OPENAI_API_KEY` duoc cau hinh. Endpoint nay chi soan note ho tro reviewer, khong tu gan nhan, khong xac nhan ground truth va khong thay the human review.

## Deliverables

- Candidate manifest.
- Annotation export.
- Coverage report.
- Dataset card.
- Validation report.
- Artifact checklist.
- Checksums.
- Release notes.

## Planning Docs

- [Ke hoach 3 tuan](docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md)
- [Data contracts](docs/05-data-contracts.md)
- [Runbook](docs/16-runbook.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA.md)
