# Candidate Mining

Python CLI tao inventory, proxy clips va candidate manifest.

## Usage

```bash
PYTHONPATH=apps/candidate-mining/src:. python3 -m candidate_mining.cli \
  --input data/raw/sample.mp4 \
  --events data/samples/candidate-events.sample.json \
  --output outputs/runs/demo \
  --random-seed 42
```

## Input Event Format

```json
{
  "events": [
    {
      "candidate_rule": "intrusion_manual_v1",
      "candidate_start_ms": 45000,
      "candidate_end_ms": 52000
    }
  ]
}
```

## Rule 30s/Event/30s

Clip event duoc cat tu:

- 30 giay truoc event.
- Toan bo duration event.
- 30 giay sau event.
- Clamp trong khoang `[0, source_video_duration_ms]`.

## Output Layout

```text
outputs/runs/{run_id}/
  inventory.json
  candidate-manifest.json
  run-summary.json
  processing.log
  clips/
```

## Limitations

- POC nhan candidate events tu JSON input, chua co detector tu dong.
- Can ffmpeg/ffprobe de xu ly video thuc.
- Khong tao ground truth.
