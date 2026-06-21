#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from advanced_ops import run  # noqa: E402

raise SystemExit(run("create-adjustment-suggestions"))

