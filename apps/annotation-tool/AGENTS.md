# Annotation Tool Instructions

## Scope

Chi xu ly:

- Load candidate manifest.
- Display clip.
- Collect human annotation.
- Save progress.
- Export annotation.

## Boundaries

- Khong sua candidate manifest.
- Khong thay doi sample_id.
- Khong tu gan confirmed neu chua co reviewer.
- Khong hard-code event labels.
- Khong ghi output vao candidate mining directory.

## Required Fields

- `sample_id`
- `event_label`
- `event_start_ms`
- `event_end_ms`
- `ground_truth_status`
- `reviewer`
- `reviewed_at`
- `comment`

## Required Tests

- Manifest hop le.
- Manifest khong hop le.
- Clip bi thieu.
- Timestamp sai.
- Label sai.
- Resume annotation.
- Export annotation.
- Schema validation.
