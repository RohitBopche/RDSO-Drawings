"""Gate V as a test: the pilot checklist passes for every manual (the determinism line is skipped here; CI rebuilds)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pilot_checklist_has_no_failing_line():
    r = subprocess.run([sys.executable, "scripts/pilot_checklist.py"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "0 fail" in r.stdout
