"""Compatibility layer for older imports."""

import sys
from pathlib import Path


root = Path(__file__).parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from policymind.models.schemas import *  # noqa: F401,F403