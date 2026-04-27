"""Compatibility layer for older imports."""

import sys
from pathlib import Path


root = Path(__file__).parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from policymind.core.config import Settings
from policymind.services.document_processor import DocumentProcessor as _DocumentProcessor


class DocumentProcessor(_DocumentProcessor):
    def __init__(self):
        super().__init__(Settings())

