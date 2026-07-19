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

## Detect-to-Candidate Usage

Sau khi co `outputs/reports/triage-report.json` hoac report tu web triage:

```bash
PYTHONPATH=apps/candidate-mining/src:.:scripts .venv/bin/python scripts/mine_from_triage.py \
  --triage outputs/reports/triage-report.json \
  --output-root outputs/runs \
  --padding-ms 30000 \
  --random-seed 42
```

Rule `person_detected_v1` chi tao candidate clips tu timestamp detector thay nguoi.
Human reviewer van phai gan `event_label` va `ground_truth_status`.

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

- CLI chinh van nhan candidate events tu JSON input.
- Detect-to-candidate chi ho tro person detector triage, khong tu gan ground truth.
- Can ffmpeg/ffprobe de xu ly video thuc.
- Khong tao ground truth.
