"""Tests for history export (CSV / JSON)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.core.export import export_history_csv, export_history_json

HISTORY = [
    {"net_wpm": 42.5, "accuracy": 96.0, "duration_seconds": 60,
     "timestamp": "2026-11-10T10:00:00"},
    {"net_wpm": 51.0, "accuracy": 97.5, "duration_seconds": 180,
     "timestamp": "2026-11-10T11:00:00"},
]


class TestExport:
    def test_json_roundtrip(self, tmp_path: Path) -> None:
        target = tmp_path / "h.json"
        export_history_json(HISTORY, target)
        assert json.loads(target.read_text(encoding="utf-8")) == HISTORY

    def test_csv_headers_and_rows(self, tmp_path: Path) -> None:
        target = tmp_path / "h.csv"
        export_history_csv(HISTORY, target)
        rows = list(csv.reader(target.open(encoding="utf-8")))
        assert rows[0] == ["accuracy", "duration_seconds", "net_wpm", "timestamp"]
        assert len(rows) == 3

    def test_empty_history_writes_empty_csv(self, tmp_path: Path) -> None:
        target = tmp_path / "empty.csv"
        export_history_csv([], target)
        assert target.read_text(encoding="utf-8") == ""

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "sub" / "dir" / "h.json"
        export_history_json(HISTORY, target)
        assert target.exists()
