#!/usr/bin/env python3
"""Generated Selenium automation template."""

import argparse
import json
import logging


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(json.dumps({"dry_run": not args.execute}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
