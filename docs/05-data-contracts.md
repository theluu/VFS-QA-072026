# Data Contracts

## Candidate Manifest

Top-level fields:

- `schema_version`
- `dataset_id`
- `manifest_id`
- `generated_at`
- `generator_version`
- `random_seed`
- `samples`

Sample fields:

- `sample_id`
- `source_video_id`
- `source_video_path`
- `source_video_duration_ms`
- `clip_path`
- `clip_type`
- `candidate_rule`
- `start_ms`
- `end_ms`
- `duration_ms`
- `metadata`

Rules:

- `sample_id` bat buoc duy nhat.
- `sample_id` khong doi giua cac lan chay cung input va config.
- `clip_type` gom `event` hoac `background`.
- `candidate_rule` ghi rule tao sample.
- `duration_ms = end_ms - start_ms`.
- Duong dan phai tuong doi so voi project root hoac dataset root.

Format `sample_id`:

```text
{source_video_id}__{start_ms}__{end_ms}__{candidate_rule_version}
```

## Annotation Export

Top-level fields:

- `schema_version`
- `dataset_id`
- `annotation_batch_id`
- `exported_at`
- `annotations`

Annotation fields:

- `sample_id`
- `event_label`
- `event_start_ms`
- `event_end_ms`
- `ground_truth_status`
- `reviewer`
- `reviewed_at`
- `comment`
- `annotation_version`

`ground_truth_status`:

```text
unreviewed
confirmed
rejected
needs_review
```

## Relationship

- Mot candidate sample co toi da mot annotation active trong mot export.
- Annotation phai tham chieu `sample_id` ton tai.
- Khong duoc export annotation orphan.
- Annotation sua lai phai tang `annotation_version`.
