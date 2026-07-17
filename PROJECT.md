# Project Overview

## Problem Statement

Nhom can mot POC de chuan bi du lieu test va ground truth cho AI Camera an ninh vanh dai. Model AI nam ngoai pham vi repo; repo nay tap trung vao candidate mining, human annotation, validation va artifact ban giao co the truy vet.

## Project Objectives

- Nhan it nhat mot video dau vao.
- Tao inventory video.
- Tao candidate clips theo rule.
- Sinh candidate manifest hop le.
- Cho phep nguoi dung gan nhan thu cong.
- Export annotation hop le.
- Sinh coverage report.
- Sinh dataset card.
- Dam bao pipeline co the tai chay.

## Users and Stakeholders

- A: QA Lead / Test Design, review coverage va artifact.
- B: Data & Automation, tao inventory, candidates, clips va manifest.
- C: Annotation & Data Quality, gan nhan va khoa ground truth.
- Mentor/stakeholder: phe duyet pass/fail va rule nghiep vu.

## Workflow

```text
Raw video -> Inventory -> Candidate mining -> Proxy clips
-> Candidate manifest -> Annotation tool -> Annotation export
-> Validation -> Coverage report -> Release package
```

## Input

- Video local trong `data/raw/` hoac duong dan local hop le.
- Candidate events JSON neu POC chua co detector tu dong.
- Config label va status trong `configs/`.

## Processing

- Doc metadata bang ffprobe.
- Cat clip bang ffmpeg.
- Sinh `sample_id` deterministic.
- Validate manifest va annotation theo schema.
- Luu output vao `outputs/`.

## Output

- Inventory JSON.
- Candidate manifest JSON.
- Proxy clips.
- Annotation export JSON.
- Coverage report JSON.
- Dataset card va release artifacts.

## Deliverables

- Code FastAPI backend.
- React annotation UI.
- Candidate mining CLI.
- JSON Schema va sample JSON.
- Validation/reporting scripts.
- Tai lieu runbook, guideline va checklist.

## Technical Constraints

- Backend dung Python + FastAPI.
- Frontend dung React JS.
- Video processing dung ffprobe/ffmpeg.
- LLM helper chi ho tro soan goi y review note, khong tu dong tao ground truth.
- Duong dan artifact luu trong JSON phai la relative path.

## Data Constraints

- Khong commit raw video hoac output nhay cam.
- Khong ghi de video nguon.
- Timestamp dung integer millisecond.
- `sample_id` phai duy nhat va tai tao duoc.

## Success Criteria

- `make lint`, `make test`, `make validate-schemas`, `make validate-samples` pass.
- Manifest va annotation sample validate thanh cong.
- UI load duoc manifest, xem metadata, gan nhan va export.
- CLI sinh manifest va clips tu video thuc khi co ffmpeg/ffprobe.

## Non-goals

- Khong huan luyen model.
- Khong auto-label thay con nguoi.
- Khong real-time camera processing.
- Khong cloud production deployment.
- Khong nhan dang danh tinh.

## Known Risks

- Candidate event source chua duoc chot.
- KPI precision/recall can predicted alerts de tinh dung.
- Du lieu that co the chua duoc phep commit hoac chia se.
- FastAPI/React dependencies can duoc cai truoc khi chay server.
