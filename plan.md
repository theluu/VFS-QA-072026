# Cấu trúc Markdown điều phối Codex

## AI Camera Candidate Mining & Annotation Dataset POC

## 1. Lệnh tạo skeleton ban đầu

Chạy tại thư mục gốc hiện tại:

```bash
git init

mkdir -p \
  apps/candidate-mining \
  apps/annotation-tool \
  shared/schemas \
  configs \
  scripts \
  tests \
  docs/weekly \
  data/raw \
  data/interim \
  data/processed \
  data/samples \
  outputs/inventories \
  outputs/manifests \
  outputs/clips \
  outputs/annotations \
  outputs/reports \
  outputs/releases

touch \
  AGENTS.md \
  README.md \
  PROJECT.md \
  PLANS.md \
  TASKS.md \
  ACCEPTANCE_CRITERIA.md \
  DECISIONS.md \
  CHANGELOG.md \
  apps/candidate-mining/AGENTS.md \
  apps/candidate-mining/README.md \
  apps/candidate-mining/TASKS.md \
  apps/annotation-tool/AGENTS.md \
  apps/annotation-tool/README.md \
  apps/annotation-tool/TASKS.md \
  shared/README.md \
  shared/schemas/AGENTS.md \
  shared/schemas/README.md \
  configs/README.md \
  scripts/README.md \
  tests/README.md \
  data/README.md \
  outputs/README.md \
  docs/00-current-state.md \
  docs/01-business-requirements.md \
  docs/02-scope-and-non-goals.md \
  docs/03-workflow-and-ownership.md \
  docs/04-architecture.md \
  docs/05-data-contracts.md \
  docs/06-candidate-mining-spec.md \
  docs/07-annotation-tool-spec.md \
  docs/08-labeling-guideline.md \
  docs/09-event-boundary-rules.md \
  docs/10-validation-rules.md \
  docs/11-testing-strategy.md \
  docs/12-kpi-and-coverage.md \
  docs/13-dataset-card-template.md \
  docs/14-assumptions-blockers.md \
  docs/15-security-privacy.md \
  docs/16-runbook.md \
  docs/17-release-checklist.md \
  docs/18-codex-workflow.md \
  docs/19-glossary.md \
  docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md \
  docs/weekly/week-01.md \
  docs/weekly/week-02.md \
  docs/weekly/week-03.md
```

Ngoài các file Markdown, Codex cần tạo tiếp:

```text
.gitignore
pyproject.toml
Makefile
docker-compose.yml
shared/schemas/candidate-manifest.schema.json
shared/schemas/annotation-export.schema.json
shared/schemas/coverage-report.schema.json
data/samples/candidate-manifest.sample.json
data/samples/annotation-export.sample.json
```

---

# 2. Cấu trúc repo hoàn chỉnh

```text
.
├── AGENTS.md
├── README.md
├── PROJECT.md
├── PLANS.md
├── TASKS.md
├── ACCEPTANCE_CRITERIA.md
├── DECISIONS.md
├── CHANGELOG.md
├── .gitignore
├── pyproject.toml
├── Makefile
├── docker-compose.yml
│
├── apps/
│   ├── candidate-mining/
│   │   ├── AGENTS.md
│   │   ├── README.md
│   │   └── TASKS.md
│   │
│   └── annotation-tool/
│       ├── AGENTS.md
│       ├── README.md
│       └── TASKS.md
│
├── shared/
│   ├── README.md
│   └── schemas/
│       ├── AGENTS.md
│       ├── README.md
│       ├── candidate-manifest.schema.json
│       ├── annotation-export.schema.json
│       └── coverage-report.schema.json
│
├── configs/
│   └── README.md
│
├── scripts/
│   └── README.md
│
├── tests/
│   └── README.md
│
├── data/
│   ├── README.md
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── samples/
│       ├── candidate-manifest.sample.json
│       └── annotation-export.sample.json
│
├── outputs/
│   ├── README.md
│   ├── inventories/
│   ├── manifests/
│   ├── clips/
│   ├── annotations/
│   ├── reports/
│   └── releases/
│
└── docs/
    ├── 00-current-state.md
    ├── 01-business-requirements.md
    ├── 02-scope-and-non-goals.md
    ├── 03-workflow-and-ownership.md
    ├── 04-architecture.md
    ├── 05-data-contracts.md
    ├── 06-candidate-mining-spec.md
    ├── 07-annotation-tool-spec.md
    ├── 08-labeling-guideline.md
    ├── 09-event-boundary-rules.md
    ├── 10-validation-rules.md
    ├── 11-testing-strategy.md
    ├── 12-kpi-and-coverage.md
    ├── 13-dataset-card-template.md
    ├── 14-assumptions-blockers.md
    ├── 15-security-privacy.md
    ├── 16-runbook.md
    ├── 17-release-checklist.md
    ├── 18-codex-workflow.md
    ├── 19-glossary.md
    ├── ke-hoach-3-tuan-kiem-thu-ai-camera.md
    └── weekly/
        ├── week-01.md
        ├── week-02.md
        └── week-03.md
```

---

# 3. Thứ tự ưu tiên tài liệu

Codex phải coi tài liệu theo thứ tự:

1. `AGENTS.md`
2. `PROJECT.md`
3. `docs/01-business-requirements.md`
4. `docs/02-scope-and-non-goals.md`
5. `docs/05-data-contracts.md`
6. JSON Schema trong `shared/schemas/`
7. Spec của từng ứng dụng
8. `ACCEPTANCE_CRITERIA.md`
9. `PLANS.md`
10. `TASKS.md`
11. `DECISIONS.md`
12. `CHANGELOG.md`

Khi tài liệu mâu thuẫn:

* Data contract và JSON Schema được ưu tiên hơn code hiện tại.
* Business requirement được ưu tiên hơn README cũ.
* Codex không tự đoán yêu cầu.
* Codex phải ghi vấn đề vào `docs/14-assumptions-blockers.md`.

---

# 4. Nội dung bắt buộc của từng file

## `AGENTS.md`

Đây là file quan trọng nhất, điều khiển toàn bộ hành vi của Codex.

````markdown
# AGENTS.md

## Project mission

Xây dựng POC phục vụ quy trình:

1. Nhận video đầu vào.
2. Khai phá candidate clips.
3. Sinh candidate manifest theo JSON Schema.
4. Cho phép con người xem và gán nhãn.
5. Export annotation có thể kiểm tra và tái lập.
6. Sinh coverage report và dataset card.

## Required reading order

Trước khi sửa code, phải đọc:

1. PROJECT.md
2. docs/00-current-state.md
3. docs/01-business-requirements.md
4. docs/02-scope-and-non-goals.md
5. docs/05-data-contracts.md
6. ACCEPTANCE_CRITERIA.md
7. PLANS.md
8. TASKS.md
9. AGENTS.md gần nhất trong thư mục đang sửa

## Source of truth

- JSON Schema là nguồn chuẩn cho format dữ liệu.
- PROJECT.md là nguồn chuẩn cho mục tiêu dự án.
- ACCEPTANCE_CRITERIA.md là nguồn chuẩn để xác định hoàn thành.
- DECISIONS.md là nguồn chuẩn cho các quyết định kỹ thuật đã chốt.
- TASKS.md là nguồn chuẩn cho trạng thái công việc hiện tại.

## Non-negotiable rules

- Không thay đổi schema mà không cập nhật schema version.
- Không thay đổi schema mà không cập nhật sample JSON và test.
- sample_id phải duy nhất, ổn định và có thể tái tạo.
- Không dùng tên file ngẫu nhiên làm sample_id.
- Không ghi đè video gốc trong data/raw.
- Không commit video thật hoặc dữ liệu nhạy cảm vào Git.
- Tất cả đường dẫn lưu trong manifest phải là đường dẫn tương đối.
- Timestamp phải dùng integer millisecond.
- start_ms phải nhỏ hơn end_ms.
- end_ms không được vượt quá duration_ms của video nguồn.
- Mọi quá trình random sampling phải nhận random_seed.
- Không hard-code event label trong giao diện.
- Event label phải được đọc từ config.
- Không tự thêm framework hoặc service ngoài phạm vi POC.
- Không refactor ngoài phạm vi task hiện tại.
- Không đánh dấu task hoàn thành nếu chưa chạy validation và test.
- Không bỏ qua lỗi bằng try/except rỗng.
- Không tạo dữ liệu giả mà không đánh dấu rõ là sample hoặc fixture.

## Implementation workflow

Với mỗi task:

1. Đọc tài liệu liên quan.
2. Kiểm tra dependency của task.
3. Ghi kế hoạch ngắn vào TASKS.md.
4. Thực hiện thay đổi nhỏ nhất đáp ứng yêu cầu.
5. Thêm hoặc cập nhật test.
6. Chạy lint, unit test và schema validation.
7. Kiểm tra output thực tế.
8. Cập nhật TASKS.md.
9. Cập nhật CHANGELOG.md.
10. Cập nhật DECISIONS.md nếu có quyết định kiến trúc.

## Required quality checks

Sau khi bootstrap hoàn thành, phải chạy:

```bash
make lint
make test
make validate-schemas
make validate-samples
````

Nếu chưa có Makefile, task đầu tiên phải tạo Makefile và các command trên.

## Definition of done

Một task chỉ được hoàn thành khi:

* Code chạy được.
* Có test cho logic chính.
* Không phá schema hiện tại.
* Sample JSON validate thành công.
* Tài liệu liên quan đã được cập nhật.
* Có command tái hiện kết quả.
* Không còn placeholder hoặc TODO không được ghi nhận.
* Output được ghi đúng thư mục outputs/.
* TASKS.md có evidence về test đã chạy.

## Forbidden actions

* Không xóa dữ liệu trong data/raw.
* Không sửa video nguồn.
* Không thay đổi sample_id đã phát hành.
* Không đổi tên field schema tùy ý.
* Không tạo output bên ngoài outputs/.
* Không commit secrets, token hoặc đường dẫn máy cá nhân.
* Không đánh dấu PASS khi command kiểm thử chưa được chạy.

````

---

## `README.md`

Chỉ đóng vai trò hướng dẫn nhanh cho con người.

Bắt buộc có:

- Mục tiêu dự án.
- Sơ đồ B → C → A/B.
- Cấu trúc thư mục.
- Yêu cầu môi trường.
- Cách setup.
- Cách chạy candidate mining.
- Cách chạy annotation tool.
- Cách validate dữ liệu.
- Cách chạy test.
- Link đến `docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md`.
- Danh sách deliverables.

Không đưa toàn bộ requirement vào README.

---

## `PROJECT.md`

Là bản mô tả dự án ổn định.

Các mục:

```markdown
# Project overview

## Problem statement

## Project objectives

## Users and stakeholders

## Workflow

## Input

## Processing

## Output

## Deliverables

## Technical constraints

## Data constraints

## Success criteria

## Non-goals

## Known risks
````

Các mục tiêu chính:

* Nhận ít nhất một video đầu vào.
* Tạo inventory video.
* Tạo candidate clips theo rule.
* Sinh manifest hợp lệ.
* Cho phép người dùng gán nhãn.
* Export annotation hợp lệ.
* Sinh coverage report.
* Sinh dataset card.
* Toàn bộ pipeline có thể tái chạy.

---

## `PLANS.md`

Quản lý kế hoạch triển khai nhiều phase.

```markdown
# Implementation plans

## Plan rules

- Chỉ thực hiện một phase tại một thời điểm.
- Mỗi phase phải có input, output và exit criteria.
- Không bắt đầu phase tiếp theo khi exit criteria chưa đạt.
- Mỗi thay đổi scope phải ghi vào DECISIONS.md.
- Mỗi blocker phải ghi vào docs/14-assumptions-blockers.md.

## Phase 0 — Repository bootstrap

### Goal

Tạo Git repository và skeleton đúng theo tài liệu.

### Outputs

- Git repository.
- Cấu trúc thư mục.
- AGENTS.md.
- PROJECT.md.
- PLANS.md.
- TASKS.md.
- README được sửa link.
- File kế hoạch ba tuần tồn tại.
- pyproject.toml.
- Makefile.
- .gitignore.

### Exit criteria

- git status chạy thành công.
- Không còn link Markdown trỏ tới file không tồn tại.
- Các thư mục chính đều có README.md.
- make test chạy được, kể cả khi mới chỉ có smoke test.

## Phase 1 — Data contracts

### Goal

Chốt contract B → C và C → A/B.

### Outputs

- candidate-manifest.schema.json.
- annotation-export.schema.json.
- coverage-report.schema.json.
- Sample JSON.
- Schema validation script.
- Unit tests.

### Exit criteria

- Sample JSON validate thành công.
- sample_id uniqueness được kiểm tra.
- Timestamp validation hoạt động.
- Invalid fixtures bị reject.

## Phase 2 — Candidate mining POC

### Goal

Nhận một video và sinh inventory, manifest, event clips và background clips.

### Outputs

- Video inventory.
- Candidate manifest.
- Proxy clips.
- Processing log.
- CLI command.
- Unit tests.

### Exit criteria

- Chạy được với một video mẫu.
- Clip path trong manifest tồn tại.
- Clip duration đúng rule.
- Random background tái lập được bằng random_seed.
- Manifest validate thành công.

## Phase 3 — Annotation tool POC

### Goal

Load manifest, xem clip và gán nhãn.

### Outputs

- Clip viewer.
- Annotation form.
- Save progress.
- Annotation export.
- Validation trước khi export.

### Exit criteria

- Load được manifest hợp lệ.
- Hiển thị được clip.
- Gán được event_label.
- Gán được event_start_ms và event_end_ms.
- Gán được ground_truth_status.
- Lưu reviewer và comment.
- Export validate theo schema.

## Phase 4 — Validation and reporting

### Goal

Kiểm tra toàn vẹn dataset và sinh báo cáo.

### Outputs

- Dataset validator.
- Coverage report.
- Error report.
- KPI summary.
- Automated tests.

### Exit criteria

- Phát hiện duplicate sample_id.
- Phát hiện timestamp sai.
- Phát hiện clip không tồn tại.
- Phát hiện label không hợp lệ.
- Coverage report validate theo schema.

## Phase 5 — Release v1

### Goal

Đóng gói artifact bàn giao.

### Outputs

- Candidate manifest.
- Annotation export.
- Coverage report.
- Dataset card.
- Release checklist.
- Runbook.
- Versioned release folder.

### Exit criteria

- Tất cả acceptance criteria đạt.
- Tất cả test pass.
- Không có blocker mức critical.
- Artifact có checksum.
- Có command tái hiện pipeline.
```

---

## `TASKS.md`

Quản lý backlog thực tế cho Codex.

Mỗi task theo format:

````markdown
## P0-001 — Initialize Git repository

Status: TODO

Priority: Critical

Dependencies: None

Files:

- .git/
- .gitignore
- README.md

Acceptance:

- git status chạy thành công.
- Branch mặc định được tạo.
- Không commit video và output sinh tự động.

Validation:

```bash
git status
git check-ignore data/raw/sample.mp4
````

Evidence:

* Chưa thực hiện.

````

Trạng thái hợp lệ:

```text
TODO
IN_PROGRESS
BLOCKED
REVIEW
DONE
````

Codex không được dùng trạng thái khác.

---

## `ACCEPTANCE_CRITERIA.md`

Chứa tiêu chí nghiệm thu toàn dự án.

### Repository

* Git repository tồn tại.
* Các thư mục trong README tồn tại.
* File kế hoạch ba tuần tồn tại.
* Link nội bộ không bị hỏng.
* Có `.gitignore`.
* Có command setup và test.

### Data contract

* Có schema cho candidate manifest.
* Có schema cho annotation export.
* Có schema cho coverage report.
* Có sample hợp lệ.
* Có fixtures không hợp lệ để test.
* Schema có version.

### Candidate mining

* Nhận được một video.
* Đọc được metadata video.
* Sinh inventory.
* Sinh event clips.
* Sinh background clips.
* Sinh manifest.
* Có random seed.
* Clip không vượt khỏi video nguồn.
* Manifest validate thành công.

### Annotation tool

* Load manifest.
* Xem clip.
* Chuyển clip trước và sau.
* Gán event label.
* Gán timestamp.
* Gán ground-truth status.
* Ghi reviewer.
* Ghi comment.
* Lưu tiến độ.
* Export annotation.

### Validation

* Kiểm tra sample_id duy nhất.
* Kiểm tra timestamp.
* Kiểm tra clip path.
* Kiểm tra label.
* Kiểm tra schema version.
* Kiểm tra annotation không tham chiếu sample không tồn tại.

### Deliverables

* Candidate manifest.
* Annotation export.
* Coverage report.
* Dataset card.
* Artifact checklist.
* Release notes.
* Runbook.

---

## `DECISIONS.md`

Ghi các quyết định kỹ thuật theo dạng ADR ngắn.

```markdown
## ADR-001 — Timestamp unit

Status: Accepted

Date: YYYY-MM-DD

Context:

Timestamp dạng số thực theo giây có thể tạo sai lệch khi serialize và so sánh.

Decision:

Toàn bộ timestamp sử dụng integer millisecond:

- start_ms
- end_ms
- duration_ms

Consequences:

- Validation đơn giản hơn.
- Không có sai số float.
- Annotation tool phải chuyển thời gian video sang millisecond.
```

Các quyết định bắt buộc ghi:

* Quy tắc sinh `sample_id`.
* Đơn vị timestamp.
* Schema versioning.
* Công nghệ annotation tool.
* Cách cắt proxy clips.
* Random sampling.
* Cách lưu annotation progress.
* Quy tắc dataset release.

---

## `CHANGELOG.md`

Theo format:

```markdown
# Changelog

## Unreleased

### Added

### Changed

### Fixed

### Removed
```

Chỉ ghi thay đổi đã thực hiện, không ghi kế hoạch.

---

# 5. Tài liệu nghiệp vụ trong `docs/`

## `docs/00-current-state.md`

Ghi nguyên trạng repo lúc bắt đầu:

* Repo chỉ có tài liệu và ảnh tuần 1/2/3.
* Chưa có `apps/`, `shared/`, `configs/`, `scripts/`, `data/`, `outputs/`, `docs/`.
* README trỏ tới file không tồn tại.
* Thư mục chưa phải Git repository.
* Chưa có schema.
* Chưa có source code.
* Chưa có test.
* Chưa có sample dataset chuẩn.

File này giúp Codex không hiểu nhầm rằng code cũ đã tồn tại.

---

## `docs/01-business-requirements.md`

Các mục:

* Bài toán cần giải quyết.
* Người sử dụng.
* Vai trò A, B, C.
* Input của từng bước.
* Output của từng bước.
* Luồng B → C.
* Luồng C → A/B.
* Deliverables.
* KPI nghiệp vụ.
* Điều kiện cần con người can thiệp.
* Các trường hợp chưa rõ.

---

## `docs/02-scope-and-non-goals.md`

### In scope

* Một video đầu vào.
* Video inventory.
* Candidate mining theo rule.
* Proxy clips.
* Random background clips.
* Candidate manifest.
* Annotation viewer.
* Manual labeling.
* Annotation export.
* Schema validation.
* Coverage report.
* Dataset card.

### Out of scope v1

* Model production.
* Training pipeline hoàn chỉnh.
* Auto-label không cần con người.
* Multi-user permission phức tạp.
* Cloud deployment production.
* Distributed processing.
* Real-time camera processing.
* Face recognition.
* Tracking danh tính con người.
* Video streaming quy mô lớn.

---

## `docs/03-workflow-and-ownership.md`

Mô tả trách nhiệm:

### B — Candidate mining

* Nhận video.
* Lập inventory.
* Tạo candidate clips.
* Sinh candidate manifest.
* Bảo đảm `sample_id` ổn định.

### C — Annotation

* Nhận candidate manifest.
* Xem clip.
* Gán nhãn.
* Chỉnh event boundary.
* Ghi trạng thái ground truth.
* Export annotation.

### A/B — Consumer

* Nhận annotation export.
* Dùng dữ liệu cho đánh giá, huấn luyện hoặc phân tích.
* Không tự thay đổi ground truth mà không qua review.

---

## `docs/04-architecture.md`

Bắt buộc có sơ đồ:

```text
Raw Video
    |
    v
Video Inventory
    |
    v
Candidate Mining
    |
    +----> Event Proxy Clips
    |
    +----> Random Background Clips
    |
    v
Candidate Manifest
    |
    v
Annotation Tool
    |
    v
Annotation Export
    |
    +----> Dataset Validator
    |
    +----> Coverage Report
    |
    +----> Dataset Card
```

Các phần cần mô tả:

* Component.
* Input/output.
* Dependency.
* Failure handling.
* File storage.
* Logging.
* Configuration.
* Test boundary.

---

## `docs/05-data-contracts.md`

Đây là tài liệu quan trọng nhất sau `AGENTS.md`.

### Candidate manifest

Field đề xuất:

```text
schema_version
dataset_id
manifest_id
generated_at
generator_version
random_seed
sample_id
source_video_id
source_video_path
source_video_duration_ms
clip_path
clip_type
candidate_rule
start_ms
end_ms
duration_ms
metadata
```

Quy tắc:

* `sample_id` bắt buộc duy nhất.
* `sample_id` không đổi giữa các lần chạy cùng input và config.
* `clip_type` gồm `event` hoặc `background`.
* `candidate_rule` ghi rule tạo sample.
* `duration_ms = end_ms - start_ms`.
* Đường dẫn phải tương đối so với project root hoặc dataset root.

Format `sample_id` đề xuất:

```text
{source_video_id}__{start_ms}__{end_ms}__{candidate_rule_version}
```

### Annotation export

Field đề xuất:

```text
schema_version
dataset_id
annotation_batch_id
exported_at
sample_id
event_label
event_start_ms
event_end_ms
ground_truth_status
reviewer
reviewed_at
comment
annotation_version
```

`ground_truth_status`:

```text
unreviewed
confirmed
rejected
needs_review
```

### Quan hệ dữ liệu

* Một candidate sample có tối đa một annotation active trong một export.
* Annotation phải tham chiếu `sample_id` tồn tại.
* Không được export annotation orphan.
* Annotation sửa lại phải tăng `annotation_version`.

---

## `docs/06-candidate-mining-spec.md`

Mô tả chính xác:

### Input

* Video path.
* Output directory.
* Clip duration.
* Event timestamps hoặc candidate events.
* Background sample count.
* Random seed.
* Candidate rule version.

### Process

1. Validate video.
2. Đọc metadata bằng `ffprobe`.
3. Sinh inventory.
4. Chuẩn hóa event boundary.
5. Cắt proxy clip.
6. Random background ngoài vùng event.
7. Sinh `sample_id`.
8. Sinh manifest.
9. Validate manifest.
10. Sinh processing summary.

### Rule 30s/event/30s

Phải ghi rõ cách hiểu:

* 30 giây trước event.
* Phần event.
* 30 giây sau event.
* Clamp về khoảng hợp lệ của video.
* Không để timestamp âm.
* Không để end vượt duration.
* Quy định xử lý event gần nhau.
* Quy định xử lý clip overlap.

### Output

* Inventory JSON.
* Candidate manifest JSON.
* Proxy clips.
* Log.
* Summary report.

---

## `docs/07-annotation-tool-spec.md`

### Chức năng bắt buộc

* Chọn manifest.
* Validate manifest khi load.
* Hiển thị clip.
* Hiển thị sample metadata.
* Previous/next sample.
* Chọn event label.
* Nhập event start/end.
* Chọn ground-truth status.
* Nhập reviewer.
* Nhập comment.
* Save progress.
* Resume progress.
* Export annotation.
* Validate trước export.

### Không hard-code

* Label list.
* Status list.
* Dataset path.
* Output path.
* Reviewer name.

Các giá trị phải đọc từ config hoặc manifest.

---

## `docs/08-labeling-guideline.md`

Mỗi label cần có:

```markdown
## Label name

### Definition

### Positive examples

### Negative examples

### Common confusion

### Boundary rule

### Required evidence

### Reviewer notes
```

Bổ sung:

* Khi nào dùng `needs_review`.
* Khi nào reject candidate.
* Khi nào clip không đủ thông tin.
* Khi nào phải xem video dài hơn.
* Không suy đoán hành vi ngoài hình ảnh quan sát được.

---

## `docs/09-event-boundary-rules.md`

Quy định:

* Định nghĩa thời điểm event bắt đầu.
* Định nghĩa thời điểm event kết thúc.
* Xử lý event bị che khuất.
* Xử lý event ra khỏi khung hình.
* Xử lý nhiều người.
* Xử lý nhiều event trong cùng clip.
* Xử lý event kéo dài hơn clip.
* Xử lý camera đổi góc.
* Sai số timestamp cho phép.
* Quy tắc escalation cho con người.

---

## `docs/10-validation-rules.md`

Validation bắt buộc:

* JSON Schema.
* `sample_id` uniqueness.
* `sample_id` không rỗng.
* Video nguồn tồn tại.
* Clip tồn tại.
* `start_ms >= 0`.
* `end_ms > start_ms`.
* `end_ms <= source_video_duration_ms`.
* `duration_ms = end_ms - start_ms`.
* Annotation tham chiếu candidate tồn tại.
* Label thuộc danh sách hợp lệ.
* Reviewer không rỗng khi status là `confirmed`.
* Không có annotation trùng active.
* Không có đường dẫn tuyệt đối.
* Schema version được hỗ trợ.

Mỗi lỗi cần có:

```text
error_code
severity
file
sample_id
field
message
suggested_fix
```

---

## `docs/11-testing-strategy.md`

Các lớp test:

### Unit test

* Sinh sample ID.
* Clamp timestamp.
* Tính duration.
* Random background.
* Schema loader.
* Annotation validator.

### Integration test

* Một video → inventory.
* Một video → clips.
* Một video → manifest.
* Manifest → annotation tool.
* Annotation → export.
* Export → coverage report.

### Contract test

* Candidate manifest sample validate.
* Annotation export sample validate.
* Invalid fixture bị reject.
* Schema backward compatibility.

### End-to-end test

```text
Sample video
→ candidate mining
→ manifest
→ manual fixture annotation
→ export
→ validation
→ coverage report
```

---

## `docs/12-kpi-and-coverage.md`

Coverage report tối thiểu:

* Tổng video.
* Tổng thời lượng video.
* Tổng candidate samples.
* Tổng event samples.
* Tổng background samples.
* Tổng samples đã review.
* Tổng samples chưa review.
* Tổng confirmed.
* Tổng rejected.
* Tổng needs review.
* Phân bố theo event label.
* Phân bố theo source video.
* Phân bố duration.
* Tỷ lệ clip path hợp lệ.
* Tỷ lệ annotation hợp lệ.
* Tỷ lệ hoàn thành labeling.

Công thức cần ghi rõ:

```text
annotation_completion_rate =
reviewed_samples / total_candidate_samples

confirmed_rate =
confirmed_samples / reviewed_samples

valid_artifact_rate =
valid_samples / total_candidate_samples
```

Không ghi `accuracy`, `precision`, `recall` hoặc `F1-score` nếu chưa có predicted label và ground truth tương ứng.

---

## `docs/13-dataset-card-template.md`

Mỗi release phải có:

* Dataset name.
* Dataset version.
* Purpose.
* Source.
* Collection period.
* Video count.
* Duration.
* Candidate generation rules.
* Annotation process.
* Label definitions.
* Reviewer process.
* Quality checks.
* Coverage.
* Known limitations.
* Bias risks.
* Privacy considerations.
* Intended use.
* Prohibited use.
* Release artifacts.
* Schema version.
* Code version.
* Random seed.
* Checksums.

---

## `docs/14-assumptions-blockers.md`

Format:

```markdown
## ASM-001 — Candidate event source

Type: Assumption

Status: Open

Impact: High

Description:

Chưa xác định candidate event được cung cấp từ file timestamp hay được phát hiện tự động.

Temporary decision:

POC nhận candidate events từ JSON input.

Owner:

Project team

Resolution deadline:

Before Phase 2
```

Phân loại:

```text
Assumption
Question
Blocker
Risk
```

---

## `docs/15-security-privacy.md`

Quy định:

* Không commit video thật.
* Không commit ảnh chứa dữ liệu nhạy cảm.
* Không commit annotation chứa thông tin cá nhân nếu chưa ẩn danh.
* Raw data ở chế độ read-only.
* Output phải có nguồn gốc.
* Không ghi token vào config.
* Không lưu đường dẫn tuyệt đối của máy người dùng.
* Không thực hiện nhận dạng danh tính.
* Có quy định retention và xóa dữ liệu.
* Dataset card phải ghi privacy limitation.

---

## `docs/16-runbook.md`

Command bắt buộc:

```bash
make setup
make lint
make test
make validate-schemas
make validate-samples
make candidate-mining INPUT=data/raw/sample.mp4
make annotation-tool
make coverage-report
make release
```

Mỗi command cần ghi:

* Mục đích.
* Input.
* Output.
* Exit code.
* Lỗi thường gặp.
* Cách khắc phục.

---

## `docs/17-release-checklist.md`

```markdown
# Release checklist

## Repository

- [ ] Git working tree sạch.
- [ ] Version đã được cập nhật.
- [ ] CHANGELOG đã được cập nhật.
- [ ] Không có secret.
- [ ] Không có raw video bị commit.

## Contracts

- [ ] Candidate manifest schema validate.
- [ ] Annotation export schema validate.
- [ ] Coverage report schema validate.
- [ ] Sample files validate.

## Tests

- [ ] Lint pass.
- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] End-to-end test pass.

## Artifacts

- [ ] Manifest tồn tại.
- [ ] Annotation export tồn tại.
- [ ] Coverage report tồn tại.
- [ ] Dataset card tồn tại.
- [ ] Artifact checklist tồn tại.
- [ ] Checksums tồn tại.

## Documentation

- [ ] README đúng.
- [ ] Runbook đúng.
- [ ] Known limitations đã ghi.
- [ ] Blocker còn lại đã ghi.
```

---

## `docs/18-codex-workflow.md`

Quy định cách giao việc cho Codex:

### Một task mỗi lần

Không yêu cầu Codex cùng lúc:

* Dựng repo.
* Thiết kế schema.
* Viết candidate mining.
* Viết annotation UI.
* Viết test.
* Release.

Phải chia theo phase.

### Trước khi code

Codex phải trả lời:

* File sẽ sửa.
* Requirement đang xử lý.
* Dependency.
* Acceptance criteria.
* Test sẽ chạy.
* Assumption phát hiện được.

### Sau khi code

Codex phải báo:

* File đã tạo.
* File đã sửa.
* Command đã chạy.
* Test pass/fail.
* Output tạo ra.
* Blocker còn lại.
* Task tiếp theo.

---

## `docs/19-glossary.md`

Định nghĩa thống nhất:

* Candidate.
* Candidate mining.
* Manifest.
* Annotation.
* Ground truth.
* Event label.
* Event boundary.
* Proxy clip.
* Background clip.
* Source video.
* Sample.
* `sample_id`.
* Reviewer.
* Coverage.
* Dataset card.
* Schema version.
* Artifact.
* Release.

---

## `docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md`

Phải tạo file này để sửa link bị thiếu trong README.

### Tuần 1

* Bootstrap repo.
* Chốt requirement.
* Chốt data contract.
* Tạo JSON Schema.
* Tạo sample files.
* Tạo validation.

### Tuần 2

* Candidate mining POC.
* Video inventory.
* Proxy clips.
* Event/background samples.
* Candidate manifest.

### Tuần 3

* Annotation tool.
* Annotation export.
* Coverage report.
* Dataset card.
* Validation.
* Release v1.

---

# 6. Markdown riêng cho từng component

## `apps/candidate-mining/AGENTS.md`

```markdown
# Candidate Mining Instructions

## Scope

Chỉ xử lý:

- Video metadata.
- Candidate event input.
- Proxy clip generation.
- Background sampling.
- Candidate manifest.

## Boundaries

- Không thực hiện annotation.
- Không tự sinh ground truth.
- Không thay đổi schema từ component này.
- Không ghi vào outputs/annotations.
- Không sửa video nguồn.

## Required outputs

- Inventory JSON.
- Candidate manifest JSON.
- Proxy clips.
- Processing report.

## Required tests

- Invalid video path.
- Video không đọc được.
- Event timestamp âm.
- Event vượt duration.
- Event overlap.
- Background sampling reproducibility.
- Duplicate sample_id.
- Missing generated clip.
```

---

## `apps/candidate-mining/README.md`

Ghi:

* CLI usage.
* Input format.
* Config.
* Rule 30s/event/30s.
* Output layout.
* Example command.
* Error codes.
* Performance limitation.

---

## `apps/candidate-mining/TASKS.md`

Chỉ chứa task của candidate mining:

```text
CM-001 Video probe
CM-002 Inventory generator
CM-003 Event boundary normalization
CM-004 Proxy clip generator
CM-005 Background sampler
CM-006 Sample ID generator
CM-007 Manifest writer
CM-008 Manifest validation
CM-009 Integration test
```

---

## `apps/annotation-tool/AGENTS.md`

```markdown
# Annotation Tool Instructions

## Scope

Chỉ xử lý:

- Load candidate manifest.
- Display clip.
- Collect human annotation.
- Save progress.
- Export annotation.

## Boundaries

- Không sửa candidate manifest.
- Không thay đổi sample_id.
- Không tự gán confirmed nếu chưa có reviewer.
- Không hard-code event labels.
- Không ghi output vào candidate mining directory.

## Required fields

- sample_id
- event_label
- event_start_ms
- event_end_ms
- ground_truth_status
- reviewer
- reviewed_at
- comment

## Required tests

- Manifest hợp lệ.
- Manifest không hợp lệ.
- Clip bị thiếu.
- Timestamp sai.
- Label sai.
- Resume annotation.
- Export annotation.
- Schema validation.
```

---

## `apps/annotation-tool/README.md`

Ghi:

* Cách chạy.
* Công nghệ UI.
* Cách load manifest.
* Keyboard shortcuts.
* Auto-save.
* Resume.
* Export.
* Validation errors.
* Storage format.

---

## `apps/annotation-tool/TASKS.md`

```text
AT-001 Manifest loader
AT-002 Manifest validator
AT-003 Clip viewer
AT-004 Annotation form
AT-005 Navigation
AT-006 Auto-save
AT-007 Resume session
AT-008 Export
AT-009 Export validation
AT-010 Integration test
```

---

# 7. README cho các thư mục dữ liệu

## `data/README.md`

Quy định:

```text
data/raw       Video gốc, read-only, không commit.
data/interim   Metadata và dữ liệu trung gian.
data/processed Dataset đã chuẩn hóa.
data/samples   Sample nhỏ dùng cho test và tài liệu.
```

Codex không được đặt output release trong `data/`.

---

## `outputs/README.md`

Quy định:

```text
outputs/inventories   Video inventory.
outputs/manifests     Candidate manifest.
outputs/clips         Proxy clips.
outputs/annotations   Annotation export.
outputs/reports       Coverage và validation report.
outputs/releases      Dataset release đóng gói.
```

Mỗi lần chạy nên tạo thư mục:

```text
outputs/runs/{run_id}/
```

Trong đó có:

```text
config.snapshot.json
processing.log
inventory.json
candidate-manifest.json
validation-report.json
run-summary.json
```

---

## `shared/schemas/README.md`

Ghi:

* Danh sách schema.
* Schema version hiện tại.
* Quy tắc backward compatibility.
* Cách validate.
* Cách nâng version.
* Mapping producer/consumer.

Producer/consumer:

```text
candidate-manifest.schema.json
Producer: candidate-mining
Consumer: annotation-tool, validator

annotation-export.schema.json
Producer: annotation-tool
Consumer: validator, A/B downstream

coverage-report.schema.json
Producer: reporting script
Consumer: project team
```

---

## `shared/schemas/AGENTS.md`

```markdown
# Schema Instructions

- Mọi schema phải có `$schema`, `$id`, `title` và `version`.
- Không đổi tên hoặc xóa field trong minor version.
- Breaking change phải tăng major version.
- Thêm field optional tăng minor version.
- Sửa mô tả không đổi version.
- Mỗi schema phải có sample hợp lệ.
- Mỗi validation rule phải có invalid fixture.
- Thay đổi schema phải cập nhật docs/05-data-contracts.md.
- Thay đổi schema phải cập nhật DECISIONS.md.
```

---

# 8. Thứ tự giao việc cho Codex

## Prompt 1 — Bootstrap repo

```text
Đọc AGENTS.md, PROJECT.md và docs/00-current-state.md.

Chỉ thực hiện Phase 0 trong PLANS.md.

Yêu cầu:

1. Khởi tạo Git repository.
2. Tạo đầy đủ skeleton thư mục.
3. Tạo các file Markdown còn thiếu.
4. Sửa README để không còn link hỏng.
5. Tạo docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md.
6. Tạo .gitignore, pyproject.toml và Makefile tối thiểu.
7. Tạo smoke test để make test chạy thành công.
8. Cập nhật TASKS.md và CHANGELOG.md.

Không triển khai candidate mining hoặc annotation tool trong task này.

Sau khi hoàn thành, chạy:

git status
make lint
make test

Báo cáo file đã tạo, command đã chạy và kết quả kiểm thử.
```

## Prompt 2 — Data contracts

```text
Đọc AGENTS.md, PROJECT.md, docs/05-data-contracts.md,
shared/schemas/AGENTS.md và ACCEPTANCE_CRITERIA.md.

Chỉ thực hiện Phase 1 trong PLANS.md.

Tạo:

1. candidate-manifest.schema.json.
2. annotation-export.schema.json.
3. coverage-report.schema.json.
4. Sample JSON hợp lệ.
5. Invalid fixtures.
6. Validation script.
7. Unit tests.

Không triển khai UI hoặc video processing.

Mọi timestamp dùng integer millisecond.
Mọi path trong manifest dùng relative path.
sample_id phải deterministic và unique.

Chạy:

make validate-schemas
make validate-samples
make test

Cập nhật TASKS.md, DECISIONS.md và CHANGELOG.md.
```

## Prompt 3 — Candidate mining POC

```text
Đọc AGENTS.md, apps/candidate-mining/AGENTS.md,
docs/06-candidate-mining-spec.md và docs/05-data-contracts.md.

Chỉ thực hiện Phase 2 trong PLANS.md.

Nhận một video và sinh:

1. Video inventory.
2. Event proxy clips.
3. Random background clips.
4. Candidate manifest.
5. Processing report.

Sử dụng ffprobe để đọc metadata và ffmpeg để cắt clip.

Mọi random operation phải dùng random_seed.
Không ghi đè video nguồn.
Không thay đổi JSON Schema.

Thêm unit test và integration test.
Chạy toàn bộ validation trước khi đánh dấu hoàn thành.
```

## Prompt 4 — Annotation POC

```text
Đọc AGENTS.md, apps/annotation-tool/AGENTS.md,
docs/07-annotation-tool-spec.md, docs/08-labeling-guideline.md
và docs/09-event-boundary-rules.md.

Chỉ thực hiện Phase 3 trong PLANS.md.

Annotation tool phải:

1. Load candidate manifest.
2. Validate manifest.
3. Hiển thị clip.
4. Cho phép gán event_label.
5. Cho phép chỉnh event_start_ms và event_end_ms.
6. Cho phép chọn ground_truth_status.
7. Lưu reviewer và comment.
8. Auto-save progress.
9. Resume session.
10. Export annotation đúng schema.

Không hard-code labels.
Không sửa candidate manifest.
Không đổi sample_id.
```

---

# 9. Quality gate bắt buộc

Codex chỉ được bàn giao khi các command sau pass:

```bash
make lint
make test
make validate-schemas
make validate-samples
```

Sau khi có pipeline:

```bash
make candidate-mining INPUT=data/raw/sample.mp4
make validate-dataset
make coverage-report
make release
```

Release v1 phải có:

```text
candidate-manifest.json
annotation-export.json
coverage-report.json
dataset-card.md
validation-report.json
artifact-checklist.md
checksums.sha256
release-notes.md
```

---

# 10. Thứ tự file cần viết nội dung trước

Ưu tiên tuyệt đối:

1. `AGENTS.md`
2. `docs/00-current-state.md`
3. `PROJECT.md`
4. `docs/01-business-requirements.md`
5. `docs/02-scope-and-non-goals.md`
6. `docs/05-data-contracts.md`
7. `shared/schemas/README.md`
8. `PLANS.md`
9. `TASKS.md`
10. `ACCEPTANCE_CRITERIA.md`
11. `docs/ke-hoach-3-tuan-kiem-thu-ai-camera.md`
12. JSON Schema và sample JSON

Chỉ bắt đầu candidate mining sau khi hai contract sau validate thành công:

```text
candidate manifest: B → C
annotation export: C → A/B
```
