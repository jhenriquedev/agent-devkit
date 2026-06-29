#!/usr/bin/env python3
"""Generated Python automation template."""

import argparse
import logging
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.info("dry_run=%s", args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
