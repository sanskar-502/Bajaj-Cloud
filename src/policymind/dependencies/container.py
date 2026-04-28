from dataclasses import dataclass
from typing import TYPE_CHECKING

from policymind.core.config import Settings

if TYPE_CHECKING:
    from policymind.services.document_processor import DocumentProcessor
    from policymind.services.vector_store import VectorStore
    from policymind.services.llm_providers import LLMProvider
    from policymind.services.query_engine import QueryEngine


@dataclass
class AppContainer:
    settings: Settings
    document_processor: "DocumentProcessor"
    vector_store: "VectorStore"
    llm_provider: "LLMProvider"
    query_engine: "QueryEngine"


def build_container() -> AppContainer:
    from policymind.services.document_processor import DocumentProcessor
    from policymind.services.llm_providers import get_llm_provider
    from policymind.services.query_engine import QueryEngine
    from policymind.services.vector_store import VectorStore

    settings = Settings()
    vector_store = VectorStore(settings)
    llm_provider = get_llm_provider(settings)
    document_processor = DocumentProcessor(settings)
    query_engine = QueryEngine(settings=settings, vector_store=vector_store, llm_provider=llm_provider)
    return AppContainer(
        settings=settings,
        document_processor=document_processor,
        vector_store=vector_store,
        llm_provider=llm_provider,
        query_engine=query_engine,
    )

