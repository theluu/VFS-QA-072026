"""Measure the person detector against human-confirmed labels.

Reports precision, recall, F1 and the confusion matrix, plus the name of every
video it got wrong - a score with no failure list is not actionable.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.person_detect import detect_persons_in_video, load_detector

REPO_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", default="data/eval/person-detection/expected.json")
    parser.add_argument("--output", default="outputs/reports/person-detector-eval.json")
    parser.add_argument("--models-root", default="models")
    parser.add_argument("--model", default="yolov4", choices=["yolov4", "mobilenet-ssd"])
    parser.add_argument("--sample-interval-ms", type=int, default=1000)
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--min-hits", type=int, default=2)
    args = parser.parse_args(argv)

    expected_path = REPO_ROOT / args.expected
    if not expected_path.exists():
        print(f"Missing {args.expected}. Run `make fetch-eval-videos` first.", file=sys.stderr)
        return 1

    spec = json.loads(expected_path.read_text(encoding="utf-8"))
    cases = [case for case in spec["videos"] if case.get("expected_has_person") is not None]
    if not cases:
        print("No labeled cases: expected_has_person is null everywhere.", file=sys.stderr)
        return 1

    try:
        net = load_detector(REPO_ROOT / args.models_root, args.model)
    except Exception as exc:
        print(f"Cannot load detector: {exc}", file=sys.stderr)
        return 1

    tp = fp = tn = fn = 0
    rows: list[dict[str, Any]] = []
    mistakes: list[str] = []

    for case in cases:
        video = REPO_ROOT / case["video_path"]
        if not video.exists():
            print(f"  MISSING {case['video_path']}", file=sys.stderr)
            return 1
        result = detect_persons_in_video(
            video,
            net,
            sample_interval_ms=args.sample_interval_ms,
            min_confidence=args.min_confidence,
            min_hits=args.min_hits,
        )
        expected = bool(case["expected_has_person"])
        predicted = result.has_person

        if expected and predicted:
            outcome, _ = "true_positive", tp
            tp += 1
        elif not expected and predicted:
            outcome = "false_positive"
            fp += 1
            mistakes.append(case["video_path"])
        elif expected and not predicted:
            outcome = "false_negative"
            fn += 1
            mistakes.append(case["video_path"])
        else:
            outcome = "true_negative"
            tn += 1

        rows.append(
            {
                "video_path": case["video_path"],
                "expected_has_person": expected,
                "predicted_has_person": predicted,
                "outcome": outcome,
                "max_confidence": round(result.max_confidence, 4),
                "frames_with_person": result.frames_with_person,
                "frames_sampled": result.frames_sampled,
                "note": case.get("note", ""),
            }
        )
        flag = "  " if outcome.startswith("true") else "<-"
        print(
            f"{flag} {Path(case['video_path']).name:28} "
            f"expected={str(expected):5} predicted={str(predicted):5} "
            f"conf={result.max_confidence:.2f}  {outcome}"
        )

    precision = rate(tp, tp + fp)
    recall = rate(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0

    report = {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "detector": args.model,
        "settings": {
            "sample_interval_ms": args.sample_interval_ms,
            "min_confidence": args.min_confidence,
            "min_hits": args.min_hits,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": rate(tp + tn, tp + tn + fp + fn),
        },
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
        },
        "mistakes": mistakes,
        "cases": rows,
    }

    output_path = REPO_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"\nprecision={precision}  recall={recall}  f1={f1}  "
        f"(TP={tp} FP={fp} TN={tn} FN={fn})"
    )
    if mistakes:
        print("Wrong on: " + ", ".join(Path(m).name for m in mistakes))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
