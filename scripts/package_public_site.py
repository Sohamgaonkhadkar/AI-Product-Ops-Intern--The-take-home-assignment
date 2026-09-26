#!/usr/bin/env python3
"""Package the generated case study and its human-QA references for static hosting.

This only copies local artifacts into case-study/. It does not publish, deploy,
open a browser, or claim that any public URL is available.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "case-study"
ASSETS = {
    ROOT / "reports/human_qa.md": SITE / "human_qa.md",
    ROOT / "data/evidence/human_qa_template.csv": SITE / "human_qa_template.csv",
}


def main() -> int:
    index = SITE / "index.html"
    if not index.is_file():
        raise FileNotFoundError("case-study/index.html is missing; render the final case study first")
    html = index.read_text(encoding="utf-8")
    for relative in ("human_qa.md", "human_qa_template.csv"):
        if relative not in html:
            raise ValueError(f"case study does not link to expected local asset {relative}")
    for source, destination in ASSETS.items():
        if not source.is_file():
            raise FileNotFoundError(f"required release asset is missing: {source.relative_to(ROOT)}")
        shutil.copyfile(source, destination)
    print("Packaged static case study and human-QA references in case-study/; no publication or deployment performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
