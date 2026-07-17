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

### Chay 1 link (khuyen nghi cho demo/test)

```bash
make app
```

Target nay build frontend roi cho FastAPI serve luon UI tinh tai `/`. Chi can mo mot link duy nhat:

```text
http://127.0.0.1:8000
```

UI va API cung origin nen khong can CORS va khong can chay hai process. Doi port:

```bash
make app API_PORT=8020
```

Khi mo, UI goi `GET /manifests` va tu load run dau tien co trong `outputs/runs/`. Neu chua co run nao thi fallback ve manifest sample. Van co the go duong dan manifest khac vao o tren cung roi bam Load.

### Che do dev (2 process, co hot-reload)

Khi sua code React can hot-reload thi chay rieng backend va Vite dev server:

```bash
make annotation-api
make annotation-tool
```

Mac dinh UI goi API tai `http://127.0.0.1:8000`. Neu port 8000 dang ban:

```bash
make annotation-api API_PORT=8020
make annotation-tool API_PORT=8020 API_BASE=http://127.0.0.1:8020 FRONTEND_PORT=5175
```

## Video Test

Tai bo video mau cong khai ve `data/raw/` (khong commit) va sinh file events tuong ung:

```bash
make fetch-videos
```

Chay candidate mining cho toan bo video trong catalog (tham so window duoc scale theo duration tung video):

```bash
make mine-all
```

Moi video ra mot run tai `outputs/runs/<ten-video>/`. Mo UI va tro vao manifest bat ky, vi du:

```text
outputs/runs/street-30s/candidate-manifest.json
```

Luu y: bo video mau la canh ngoai troi/animation cong khai, dung de kiem tra pipeline chay dung. Day khong phai footage CCTV vanh dai that va khong thay the du lieu test dai dien cho use case.

## Person Triage (Buoc 1)

Loc video tho: video nao co nguoi, video nao bi loai.

```bash
make fetch-person-model                      # tai detector, 1 lan
make triage-person                           # input mac dinh: data/raw/catalog.json
make triage-person TRIAGE_INPUT=data/raw     # hoac mot thu muc video
```

Output: `outputs/reports/triage-report.json`

```json
{
  "summary": {"total": 16, "kept": 7, "rejected": 9},
  "videos": [
    {"video_path": "data/raw/x.mp4", "has_person": true, "max_confidence": 0.91,
     "person_timestamps_ms": [3000, 6000], "decision": "keep"}
  ],
  "rejected": ["data/raw/ocean.mp4"]
}
```

Detector la MobileNet-SSD chay qua OpenCV DNN. Chon model nay vi license permissive; ultralytics YOLO la AGPL-3.0 nen khong dung cho ban thuong mai.

Tuning:

```bash
.venv/bin/python scripts/triage_person.py --min-confidence 0.6 --sample-interval-ms 500 --min-hits 3
```

### Do do chinh xac

```bash
make fetch-eval-videos    # tai video public domain co nguoi that
make eval-person          # tinh precision/recall
```

Tap eval: `data/eval/person-detection/expected.json`. Nhan do nguoi xem frame xac nhan, khong phai do tool sinh. Video khong commit, nhan thi commit.

Ket qua lan chay gan nhat (10 video, mac dinh `min_confidence=0.5`, `min_hits=2`):

| Metric | Value |
|---|---|
| precision | 0.86 |
| recall | 1.00 |
| f1 | 0.92 |
| confusion | TP=6 FP=1 TN=3 FN=0 |

Nhan dung ca 6 video co nguoi that, ke ca ca kho: nguoi chi xuat hien vai giay, nguoi trong nha may thieu sang va bi che mot phan. Sai duy nhat: video sua bien bi nhan nham la nguoi (0.99).

Output: `outputs/reports/person-detector-eval.json`, co ca danh sach video bi sai.

### Gioi han (quan trong)

Day la tin hieu **triage**, khong phai ground truth. Script khong bao gio ghi `event_label` hay `ground_truth_status` - xem ADR-005.

Tap eval chi co 10 video va **khong phai footage CCTV vanh dai**. So lieu tren chi chung minh detector nhan duoc nguoi that trong canh thong thuong. No khong du de ket luan cho camera an ninh that: goc cao, nguoi o xa, ban dem, hong ngoai deu chua duoc thu. Phai do lai tren footage that cua du an truoc khi tin.

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
