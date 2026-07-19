# Decisions

## ADR-001 - Timestamp unit

Status: Accepted

Date: 2026-07-17

Context:

Timestamp dang so thuc theo giay de gay sai lech khi serialize va so sanh.

Decision:

Toan bo timestamp trong contract dung integer millisecond:

- `start_ms`
- `end_ms`
- `duration_ms`
- `event_start_ms`
- `event_end_ms`

Consequences:

- Validation don gian hon.
- UI phai convert tu video currentTime sang millisecond.

## ADR-002 - Deterministic sample_id

Status: Accepted

Date: 2026-07-17

Context:

Candidate samples can duoc truy vet giua cac lan chay.

Decision:

`sample_id` co dang `{source_video_id}__{start_ms}__{end_ms}__{candidate_rule_version}`.

Consequences:

- Cung input va config se sinh cung ID.
- Khong dung ten file ngau nhien lam ID.

## ADR-003 - Schema versioning

Status: Accepted

Date: 2026-07-17

Context:

Producer va consumer can biet format dang doc.

Decision:

Moi schema co field top-level `schema_version`. Version hien tai la `1.0.0`.

Consequences:

- Breaking change phai tang major version.
- Script validation reject version khong ho tro.

## ADR-004 - Annotation tool technology

Status: Accepted

Date: 2026-07-17

Context:

Nguoi dung can UI local de xem clip va gan nhan.

Decision:

Dung FastAPI cho backend va React JS cho frontend.

Consequences:

- Backend cung cap manifest/config/export API.
- Frontend chi goi API va luu autosave localStorage.

## ADR-005 - LLM assistant boundary

Status: Accepted

Date: 2026-07-17

Context:

User yeu cau thu vien LLM tool, nhung repo khong duoc auto-label thay con nguoi.

Decision:

Them optional OpenAI SDK cho helper soan review note tu metadata va guideline. Helper nay khong gan `event_label`, khong dat `ground_truth_status`, va co fallback deterministic khi khong co API key.

Consequences:

- Khong can secret de chay POC.
- Nguoi review van la nguon quyet dinh ground truth.

## ADR-006 - Web triage to candidate mining boundary

Status: Accepted

Date: 2026-07-18

Context:

Nguoi dung can web local detect raw video nhu video VIRAT bbox mau va xuat output
theo luong candidate-mining hien tai.

Decision:

FastAPI app duoc phep orchestrate person triage va goi module candidate-mining de
sinh `outputs/runs/{run_id}/` gom inventory, clips, manifest, summary va log.
Detector timestamp chi tao `candidate_rule=person_detected_v1`.
FastAPI cung co the tao MP4 bbox burn-in duoi `outputs/annotated/` de reviewer
doi chieu voi ket qua detector.

Consequences:

- Annotation tool van khong sua `sample_id` va khong tu gan ground truth.
- Raw video khong bi ghi de; clips/proxy/report chi ghi duoi `outputs/`.
- Web va script `mine_from_triage.py` dung chung logic tao candidate output.
- Bbox MP4 la review artifact, khong thay the annotation export.

## ADR-007 - Person detector: Ultralytics YOLOv8 default

Status: Accepted

Date: 2026-07-19

Context:

Bbox video cu (YOLOv4 qua OpenCV-DNN) bat nguoi o xa kem hon video mau. Video mau
(tu repo VSF-Project) dung Ultralytics YOLOv8 nen bat duoc figure nho tren footage
CCTV. Truoc day YOLOv8 bi tranh vi license AGPL-3.0.

Decision:

- `yolov8` (Ultralytics, weight mac dinh `yolov8m.pt`, imgsz 1920, iou 0.45) tro
  thanh detector mac dinh cho annotate/bbox va triage. `yolov4` + `mobilenet-ssd`
  van chon duoc. (imgsz 1920 chu khong phai 640: tren VIRAT, 640 bat 0 nguoi,
  1920 bat duoc o ~0.4-0.7 confidence giong video mau. Doi lai ~2.5s/frame CPU.)
- Chap nhan trade-off AGPL-3.0 cho POC.
- YOLOv8 can torch, ma torch chua co ban cho Python 3.14 tren Intel macOS. Vi vay
  venv du an chuyen sang **Python 3.11** (`make setup`); toan bo app/UI van chay
  in-process tren env nay, UI khong doi.
- `cv2` phai dung ban `opencv-python` day du (khong headless): ultralytics goi
  `cv2.imshow` luc import, ban headless khong co. App khong thuc su goi imshow.
- torch tren Intel-macOS chi co ban 2.2.2 (build voi numpy 1.x) nen ghim
  `numpy<2`.

Consequences:

- `make setup` tao venv Python 3.11 (torch + ultralytics ~vai tram MB).
- Detection cham hon tren CPU (~0.3-0.5s/frame) nhung recall tot hon han.
- `YoloV8Detector` tra ve cung `PersonBox` chuan hoa 0..1 nen tracker, nhan,
  encode, UI deu giu nguyen.
