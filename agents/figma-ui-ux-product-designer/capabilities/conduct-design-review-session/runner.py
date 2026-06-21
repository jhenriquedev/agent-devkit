#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from design_support import run  # noqa: E402

raise SystemExit(run("conduct-design-review-session"))
