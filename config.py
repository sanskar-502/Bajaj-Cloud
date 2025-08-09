# config.py

import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    """
    Configuration class for the cloud-native RAG system.
    """
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")

    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "pinecone")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")
    
    # This new variable specifies which of Pinecone's hosted models to use.
    PINECONE_EMBEDDING_MODEL: str = os.getenv("PINECONE_EMBEDDING_MODEL", "llama-text-embed-v2")

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))

    SUPPORTED_FORMATS: List[str] = [".pdf", ".docx", ".txt", ".pptx"]
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50"))

    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self):
        self.validate()

    def validate(self):
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("LLM_PROVIDER is 'gemini', but GEMINI_API_KEY is missing.")
        if self.VECTOR_DB_TYPE == "pinecone":
            if not self.PINECONE_API_KEY:
                raise ValueError("VECTOR_DB_TYPE is 'pinecone', but PINECONE_API_KEY is missing.")
            if not self.PINECONE_EMBEDDING_MODEL:
                 raise ValueError("VECTOR_DB_TYPE is 'pinecone', but PINECONE_EMBEDDING_MODEL is missing.")