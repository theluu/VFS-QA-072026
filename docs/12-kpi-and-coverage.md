# KPI and Coverage

Coverage report toi thieu:

- Tong video.
- Tong thoi luong video.
- Tong candidate samples.
- Tong event samples.
- Tong background samples.
- Tong samples da review.
- Tong samples chua review.
- Tong confirmed.
- Tong rejected.
- Tong needs review.
- Phan bo theo event label.
- Phan bo theo source video.
- Phan bo duration.
- Ty le clip path hop le.
- Ty le annotation hop le.
- Ty le hoan thanh labeling.

Cong thuc:

```text
annotation_completion_rate = reviewed_samples / total_candidate_samples
confirmed_rate = confirmed_samples / reviewed_samples
valid_artifact_rate = valid_samples / total_candidate_samples
```

Khong ghi `accuracy`, `precision`, `recall` hoac `F1-score` neu chua co predicted label va ground truth tuong ung.
