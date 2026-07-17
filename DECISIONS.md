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
