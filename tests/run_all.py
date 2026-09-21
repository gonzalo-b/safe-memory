"""tests/run_all.py — the gate. Runs every tests/test_*.py as a subprocess.

    python3 tests/run_all.py

Streams each script's own output, then prints one combined total and exits 1
if anything failed. Standard library only.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    scripts = sorted(
        p for p in glob.glob(os.path.join(TESTS_DIR, "test_*.py"))
    )
    total_pass = 0
    total_fail = 0
    any_nonzero = False

    for script in scripts:
        name = os.path.relpath(script, HOME)
        print(f"\n### {name} ###")
        proc = subprocess.run([sys.executable, script], cwd=HOME,
                              capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            any_nonzero = True

        # Scrape the "<N> passed, <M> failed" line each script prints, so the
        # total is a sum of real counts, not a guess from exit codes.
        counted = False
        for line in reversed(proc.stdout.splitlines()):
            line = line.strip()
            if line.endswith("failed") and "passed" in line:
                parts = line.replace(",", "").split()
                try:
                    p_idx = parts.index("passed")
                    f_idx = parts.index("failed")
                    total_pass += int(parts[p_idx - 1])
                    total_fail += int(parts[f_idx - 1])
                    counted = True
                except (ValueError, IndexError):
                    pass
                break
        if not counted and proc.returncode != 0:
            total_fail += 1

    print(f"\nTOTAL: {total_pass} passed, {total_fail} failed")
    return 1 if (total_fail or any_nonzero) else 0


if __name__ == "__main__":
    sys.exit(main())
