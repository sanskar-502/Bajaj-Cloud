"""Compatibility layer exposing the FastAPI app at root."""

import sys
from pathlib import Path


root = Path(__file__).parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from policymind.app import app  # noqa: E402