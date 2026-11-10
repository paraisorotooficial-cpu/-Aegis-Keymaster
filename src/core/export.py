"""Export test history to CSV or JSON."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any


def export_history_json(history: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def export_history_csv(history: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    if history:
        fieldnames = sorted({key for entry in history for key in entry})
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history)
    path.write_text(buffer.getvalue(), encoding="utf-8")
