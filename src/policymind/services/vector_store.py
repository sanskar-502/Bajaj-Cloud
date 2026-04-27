from typing import Any, Dict, List, Optional

from pinecone import Pinecone

from policymind.core.config import Settings
from policymind.models.schemas import SearchResult


class VectorStore:
    """Pinecone-backed vector store using integrated cloud embeddings."""

    def __init__(self, settings: Settings):
        self.settings = settings
        if not (settings.VECTOR_DB_TYPE == "pinecone" and settings.PINECONE_EMBEDDING_MODEL):
            raise ValueError("Project must be configured for cloud models.")
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.embedding_model = settings.PINECONE_EMBEDDING_MODEL
        self.index = self._initialize_pinecone_integrated()

    def _initialize_pinecone_integrated(self):
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={"model": self.embedding_model, "field_map": {"text": "chunk_text"}},
            )
        return self.pc.Index(self.index_name)

    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return
        records_to_upsert = []
        for chunk in chunks:
            record = chunk.copy()
            if "id" in record:
                record["_id"] = record.pop("id")
            records_to_upsert.append(record)

        for i in range(0, len(records_to_upsert), 96):
            batch = records_to_upsert[i : i + 96]
            self.index.upsert_records(namespace="__default__", records=batch)

    def search(
        self, query: str, top_k: int, document_ids: Optional[List[str]] = None
    ) -> List[SearchResult]:
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        results = self.index.search(
            query={"inputs": {"text": query}, "top_k": top_k, "filter": filter_dict},
            fields=["chunk_text", "document_id", "chunk_id", "id", "title", "page"],
            namespace="__default__",
        )

        search_results: List[SearchResult] = []
        for match in results.get("result", {}).get("hits", []):
            metadata = match.get("fields", {})
            search_results.append(
                SearchResult(
                    content=metadata.get("chunk_text", ""),
                    metadata=metadata,
                    score=match.get("_score", 0.0),
                )
            )
        return search_results

    def delete_documents(self, document_ids: List[str]) -> None:
        if not document_ids:
            return
        self.index.delete(filter={"document_id": {"$in": document_ids}})

