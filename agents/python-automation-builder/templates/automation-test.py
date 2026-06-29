import subprocess
import sys
from pathlib import Path


def test_automation_dry_run():
    script = Path(__file__).resolve().parents[1] / "automation.py"
    result = subprocess.run([sys.executable, str(script), "--dry-run"], text=True, capture_output=True)
    assert result.returncode == 0
