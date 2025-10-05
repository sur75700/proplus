#!/usr/bin/env python3
"""Temporary clean stub for report generator (linters-friendly)."""

from __future__ import annotations
from pathlib import Path


def build_pdf(
    summary: dict,
    chart_path: Path,
    pdf_path: Path,
    goal_block: dict | None = None,
) -> None:
    """No-op placeholder; writes a tiny placeholder PDF header."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4\n% placeholder\n")


def main() -> None:
    print("Report generator is temporarily disabled.")


if __name__ == "__main__":
    main()
