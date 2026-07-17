from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from scripts.validation_core import REPO_ROOT


def load_local_env() -> None:
    env_path = Path(REPO_ROOT) / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=True)
        except Exception:
            # The LLM helper must degrade to deterministic fallback if dotenv is unavailable.
            pass


def deterministic_review_note(sample: dict[str, Any], annotation: dict[str, Any] | None = None) -> str:
    sample_id = sample.get("sample_id", "unknown")
    clip_type = sample.get("clip_type", "unknown")
    start_ms = sample.get("start_ms", "unknown")
    end_ms = sample.get("end_ms", "unknown")
    status = (annotation or {}).get("ground_truth_status", "unreviewed")
    return (
        f"Review sample {sample_id}. Clip type: {clip_type}. "
        f"Window: {start_ms}-{end_ms} ms. Current status: {status}. "
        "Confirm visible evidence, adjust event boundary if needed, and record uncertainty in comment."
    )


def draft_review_note(sample: dict[str, Any], annotation: dict[str, Any] | None = None) -> dict[str, Any]:
    load_local_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL")
    fallback = deterministic_review_note(sample, annotation)
    if not api_key or not model:
        return {
            "source": "deterministic_fallback",
            "note": fallback,
            "reason": "OPENAI_API_KEY and OPENAI_MODEL are required for LLM drafting.",
        }

    prompt = (
        "You assist a human video annotation reviewer. "
        "Do not assign labels or ground truth. Draft a short review note checklist only.\n\n"
        f"Sample: {sample}\n"
        f"Current annotation: {annotation or {}}\n"
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        if hasattr(client, "responses"):
            response = client.responses.create(model=model, input=prompt)
            note = getattr(response, "output_text", "") or fallback
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            note = response.choices[0].message.content or fallback
        return {"source": "openai", "note": note}
    except Exception as exc:
        return {
            "source": "deterministic_fallback",
            "note": fallback,
            "reason": f"LLM helper failed: {exc}",
        }
