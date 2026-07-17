# Validation Rules

Validation bat buoc:

- JSON Schema.
- `sample_id` uniqueness.
- `sample_id` khong rong.
- Video nguon ton tai neu validate dataset thuc.
- Clip ton tai neu validate artifact thuc.
- `start_ms >= 0`.
- `end_ms > start_ms`.
- `end_ms <= source_video_duration_ms`.
- `duration_ms = end_ms - start_ms`.
- Annotation tham chieu candidate ton tai.
- Label thuoc danh sach hop le.
- Reviewer khong rong khi status la `confirmed`.
- Khong co annotation trung active.
- Khong co duong dan tuyet doi.
- Schema version duoc ho tro.

Moi loi gom:

```text
error_code
severity
file
sample_id
field
message
suggested_fix
```
