import os
import sys
from pathlib import Path
from unittest.mock import patch


root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))


def test_app_imports() -> None:
    os.environ.setdefault("LLM_PROVIDER", "gemini")
    os.environ.setdefault("GEMINI_API_KEY", "dummy")
    os.environ.setdefault("VECTOR_DB_TYPE", "pinecone")
    os.environ.setdefault("PINECONE_API_KEY", "dummy")
    os.environ.setdefault("PINECONE_INDEX_NAME", "dummy-index")
    os.environ.setdefault("PINECONE_EMBEDDING_MODEL", "llama-text-embed-v2")

    with patch("policymind.dependencies.container.build_container"):
        from policymind.app import create_app

        app = create_app()
        assert app is not None
        assert app.title == "PolicyMind API"

