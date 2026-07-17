# Implementation Plans

## Plan Rules

- Chi thuc hien mot phase tai mot thoi diem.
- Moi phase phai co input, output va exit criteria.
- Khong bat dau phase tiep theo khi exit criteria chua dat, tru khi user yeu cau ro.
- Moi thay doi scope phai ghi vao DECISIONS.md.
- Moi blocker phai ghi vao docs/14-assumptions-blockers.md.

## Phase 0 - Repository Bootstrap

### Goal

Tao Git repository va skeleton dung theo `plan.md`.

### Outputs

- Git repository.
- Cau truc thu muc.
- AGENTS.md, PROJECT.md, PLANS.md, TASKS.md.
- README duoc sua link.
- File ke hoach ba tuan ton tai.
- pyproject.toml, Makefile, .gitignore.
- Smoke test.

### Exit Criteria

- `git status` chay thanh cong.
- Khong con link Markdown tro toi file khong ton tai.
- Cac thu muc chinh deu co README.md.
- `make test` chay duoc.

## Phase 1 - Data Contracts

### Goal

Chot contract B -> C va C -> A/B.

### Outputs

- `candidate-manifest.schema.json`.
- `annotation-export.schema.json`.
- `coverage-report.schema.json`.
- Sample JSON.
- Invalid fixtures.
- Validation script.
- Unit tests.

### Exit Criteria

- Sample JSON validate thanh cong.
- `sample_id` uniqueness duoc kiem tra.
- Timestamp validation hoat dong.
- Invalid fixtures bi reject.

## Phase 2 - Candidate Mining POC

### Goal

Nhan mot video va sinh inventory, manifest, event clips va background clips.

### Outputs

- Video inventory.
- Candidate manifest.
- Proxy clips.
- Processing log.
- CLI command.
- Unit tests.

### Exit Criteria

- Chay duoc voi mot video mau khi co input.
- Clip path trong manifest ton tai.
- Clip duration dung rule.
- Random background tai lap bang `random_seed`.
- Manifest validate thanh cong.

## Phase 3 - Annotation Tool POC

### Goal

Load manifest, xem clip va gan nhan.

### Outputs

- FastAPI annotation backend.
- React annotation UI.
- Clip viewer.
- Annotation form.
- Save progress.
- Annotation export.
- Validation truoc export.

### Exit Criteria

- Load duoc manifest hop le.
- Hien thi duoc clip neu file ton tai.
- Gan duoc event label, boundary, status, reviewer va comment.
- Export validate theo schema.

## Phase 4 - Validation and Reporting

### Goal

Kiem tra toan ven dataset va sinh bao cao.

### Outputs

- Dataset validator.
- Coverage report.
- Error report.
- KPI summary neu co predicted alerts.
- Automated tests.

### Exit Criteria

- Phat hien duplicate sample_id.
- Phat hien timestamp sai.
- Phat hien clip khong ton tai.
- Phat hien label khong hop le.
- Coverage report validate theo schema.

## Phase 5 - Release v1

### Goal

Dong goi artifact ban giao.

### Outputs

- Candidate manifest.
- Annotation export.
- Coverage report.
- Dataset card.
- Release checklist.
- Versioned release folder.

### Exit Criteria

- Tat ca acceptance criteria dat.
- Tat ca test pass.
- Khong co blocker critical.
- Artifact co checksum.
- Co command tai hien pipeline.
