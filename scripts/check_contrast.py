"""WCAG AA contrast audit script. Run: python scripts/check_contrast.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ui.contrast import audit_all_themes


def main() -> int:
    failures = 0
    for theme_name, results in sorted(audit_all_themes().items()):
        for result in results:
            status = "OK " if result.passes_aa else "FAIL"
            if not result.passes_aa:
                failures += 1
            print(
                f"{status} {theme_name:5s} {result.foreground:30s} "
                f"on {result.background:12s} {result.ratio:.2f}:1"
            )
    if failures:
        print(f"\n{failures} pair(s) below WCAG AA (4.5:1)")
        return 1
    print("\nAll text pairs meet WCAG AA (4.5:1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
