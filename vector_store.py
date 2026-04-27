"""Compatibility layer for older imports."""

import sys
from pathlib import Path


root = Path(__file__).parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from policymind.core.config import Settings
from policymind.services.vector_store import VectorStore as _VectorStore


class VectorStore(_VectorStore):
    def __init__(self):
        super().__init__(Settings())