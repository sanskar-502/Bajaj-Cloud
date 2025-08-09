# vector_store.py (Cloud Model Version)

from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from config import Config
from models import SearchResult

class VectorStore:
    """
    Handles data interaction with Pinecone using a cloud-based, integrated embedding model.
    """
    def __init__(self):
        self.config = Config()
        if not (self.config.VECTOR_DB_TYPE == "pinecone" and self.config.PINECONE_EMBEDDING_MODEL):
            raise ValueError("Project must be configured for cloud models.")

        self.pc = Pinecone(api_key=self.config.PINECONE_API_KEY)
        self.index_name = self.config.PINECONE_INDEX_NAME
        self.embedding_model = self.config.PINECONE_EMBEDDING_MODEL
        self.index = self._initialize_pinecone_integrated()

    def _initialize_pinecone_integrated(self):
        """Initializes a Pinecone index configured for an integrated model."""
        if self.index_name not in self.pc.list_indexes().names():
            print(f"Creating new Pinecone index '{self.index_name}' with model '{self.embedding_model}'...")
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": self.embedding_model,
                    "field_map": {"text": "chunk_text"}
                }
            )
        print("[VectorStore] Pinecone with integrated embedding model initialized successfully.")
        return self.pc.Index(self.index_name)

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Upserts raw text chunks to Pinecone."""
        if not chunks: return

        records_to_upsert = []
        for chunk in chunks:
            record = chunk.copy()
            if 'id' in record:
                record['_id'] = record.pop('id')
            records_to_upsert.append(record)
        
        for i in range(0, len(records_to_upsert), 96):
            batch = records_to_upsert[i : i + 96]
            self.index.upsert_records(records=batch, namespace="__default__")
            
        print(f"Upserted {len(records_to_upsert)} records to Pinecone.")

    def search(self, query: str, top_k: int, document_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """Searches the index using raw query text."""
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        
        results = self.index.search(
            query={
                "inputs": {"text": query},
                "top_k": top_k,
                "filter": filter_dict
            },
            fields=["chunk_text", "document_id", "chunk_id"],
            namespace="__default__"
        )
        
        search_results = []
        for match in results.get('result', {}).get('hits', []):
            metadata = match.get('fields', {})
            search_results.append(SearchResult(
                content=metadata.get("chunk_text", ""),
                metadata=metadata,
                score=match.get('_score', 0.0)
            ))
        return search_results


# In vector_store.py, inside the VectorStore class

    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Deletes vectors from the index based on their document_id metadata.
        """
        if not document_ids:
            return
        try:
            self.index.delete(filter={"document_id": {"$in": document_ids}})
            print(f"Successfully deleted documents with IDs: {document_ids} from Pinecone.")
        except Exception as e:
            print(f"Error deleting documents from Pinecone: {e}")

            