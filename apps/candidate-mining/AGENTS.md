# Candidate Mining Instructions

## Scope

Chi xu ly:

- Video metadata.
- Candidate event input.
- Proxy clip generation.
- Background sampling.
- Candidate manifest.

## Boundaries

- Khong thuc hien annotation.
- Khong tu sinh ground truth.
- Khong thay doi schema tu component nay.
- Khong ghi vao `outputs/annotations`.
- Khong sua video nguon.

## Required Outputs

- Inventory JSON.
- Candidate manifest JSON.
- Proxy clips.
- Processing report.

## Required Tests

- Invalid video path.
- Video khong doc duoc.
- Event timestamp am.
- Event vuot duration.
- Event overlap.
- Background sampling reproducibility.
- Duplicate sample_id.
- Missing generated clip.
