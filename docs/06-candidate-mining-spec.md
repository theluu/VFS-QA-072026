# Candidate Mining Spec

## Input

- Video path.
- Output directory.
- Event timestamps JSON.
- Background sample count.
- Random seed.
- Candidate rule version.

## Process

1. Validate video.
2. Doc metadata bang `ffprobe`.
3. Sinh inventory.
4. Chuan hoa event boundary.
5. Cat proxy clip.
6. Random background ngoai vung event.
7. Sinh `sample_id`.
8. Sinh manifest.
9. Validate manifest.
10. Sinh processing summary.

## Rule 30s/Event/30s

- 30 giay truoc event.
- Phan event.
- 30 giay sau event.
- Clamp ve khoang hop le cua video.
- Khong de timestamp am.
- Khong de end vuot duration.
- Event gan nhau co the overlap o POC v1; conflict duoc ghi trong metadata.
- Background windows khong giao voi exclusion windows.

## Output

- Inventory JSON.
- Candidate manifest JSON.
- Proxy clips.
- Log.
- Summary report.
