from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_external(link: str) -> bool:
    return (
        "://" in link
        or link.startswith("#")
        or link.startswith("mailto:")
        or link.startswith("app://")
        or link.startswith("file:")
    )


def main() -> int:
    errors: list[str] = []
    for path in sorted(REPO_ROOT.glob("**/*.md")):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            raw_link = match.group(1).strip()
            if is_external(raw_link):
                continue
            link = raw_link.split("#", 1)[0]
            if not link:
                continue
            target = (path.parent / link).resolve()
            try:
                target.relative_to(REPO_ROOT)
            except ValueError:
                errors.append(f"{path.relative_to(REPO_ROOT)} links outside repo: {raw_link}")
                continue
            if not target.exists():
                errors.append(f"{path.relative_to(REPO_ROOT)} has broken link: {raw_link}")
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Markdown links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
