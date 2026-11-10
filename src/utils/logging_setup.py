"""Application-wide logging configuration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO, log_dir: Path | None = None) -> None:
    """Configure root logging to stderr and, optionally, a rotating file.

    Args:
        level: Minimum level for the stderr handler.
        log_dir: When given, also write `aegis-keymaster.log` there.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(level)
    stream.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(stream)

    if log_dir is not None:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "aegis-keymaster.log", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(_FORMAT))
            root.addHandler(file_handler)
        except OSError as exc:
            root.warning("Could not open log file in %s: %s", log_dir, exc)
