#!/usr/bin/env python3
"""Extract the numbered research set from the preserved assignment Markdown."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "assignment_source.md"
OUTPUT = ROOT / "apps" / "apps.json"


def clean_cell(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"<([^>]+)>", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def first_url(text: str) -> str:
    match = re.search(r"https?://[^\s)]+", text)
    if match:
        return match.group(0).rstrip(".,;]")
    # The assignment includes bare developer hostnames as hints. Preserve them
    # as provenance and add HTTPS only as a normalized URL-shaped hint.
    bare = re.search(r"(?<![\w@])(?:[\w-]+\.)+[a-zA-Z]{2,}(?:/[^\s)]*)?", text)
    if bare:
        return "https://" + bare.group(0).rstrip(".,;]")
    return ""


def parse() -> list[dict]:
    category = None
    apps = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+\d+\.\s+(.+?)\s*$", line)
        if heading:
            category = heading.group(1)
            continue
        if not line.lstrip().startswith("|") or category is None:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        app_id = int(cells[0])
        raw_app = cells[1]
        app_name = clean_cell(raw_app)
        hint = cells[2]
        apps.append({
            "app_id": app_id,
            "app": app_name,
            "category": category,
            "website_hint": first_url(hint),
            "assignment_source_hint": clean_cell(hint),
        })
    return apps


def main() -> None:
    apps = parse()
    ids = [a["app_id"] for a in apps]
    names = [a["app"].casefold() for a in apps]
    if len(apps) != 100 or sorted(ids) != list(range(1, 101)):
        raise SystemExit(f"Expected IDs 1–100; got {len(apps)} rows and IDs {ids}")
    if len(set(names)) != len(names):
        raise SystemExit("Duplicate app names detected")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(apps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(apps)} unique apps across {len({a['category'] for a in apps})} categories → {OUTPUT}")


if __name__ == "__main__":
    main()
