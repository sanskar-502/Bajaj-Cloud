#!/usr/bin/env python3
"""Repository entrypoint for running PolicyMind from project root."""

import sys
from pathlib import Path


def _bootstrap_src_path() -> None:
    root = Path(__file__).parent
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def main() -> None:
    _bootstrap_src_path()
    from policymind.main import main as package_main

    package_main()


if __name__ == "__main__":
    main()