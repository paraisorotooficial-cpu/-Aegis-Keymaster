#!/usr/bin/env python3
"""Aegis Keymaster — entry point.

Runs both as ``python -m src.main`` and as the ``aegis-keymaster`` script.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import main

if __name__ == "__main__":
    sys.exit(main())
