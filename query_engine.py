"""Compatibility layer for older imports."""

import sys
from pathlib import Path


root = Path(__file__).parent
src_path = str(root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from policymind.core.config import Settings
from policymind.services.llm_providers import get_llm_provider
from policymind.services.query_engine import QueryEngine as _QueryEngine


class QueryEngine(_QueryEngine):
    def __init__(self, vector_store):
        settings = Settings()
        super().__init__(
            settings=settings,
            vector_store=vector_store,
            llm_provider=get_llm_provider(settings),
        )