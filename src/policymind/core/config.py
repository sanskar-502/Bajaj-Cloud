import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized runtime settings with validation and defaults."""

    def __init__(self) -> None:
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        self.VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "pinecone").lower()
        self.PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY")
        self.PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "policymind-index")
        self.PINECONE_EMBEDDING_MODEL: str = os.getenv(
            "PINECONE_EMBEDDING_MODEL", "llama-text-embed-v2"
        )
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
        self.SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))

        self.SUPPORTED_FORMATS: List[str] = [".pdf", ".docx", ".txt", ".pptx"]
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50"))

        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
        self.VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", "vector_store")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.HACKRX_TOKEN: str = os.getenv(
            "HACKRX_TOKEN",
            "a9710e8faf1eb0aa73caf8530b1bcac6889870fb4e3ef80e8bc17f380a3a83bc",
        )

        self.validate()

    def validate(self) -> None:
        if self.LLM_PROVIDER not in {"gemini", "openai"}:
            raise ValueError(f"Unsupported LLM_PROVIDER: '{self.LLM_PROVIDER}'.")

        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("LLM_PROVIDER is 'gemini', but GEMINI_API_KEY is missing.")

        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("LLM_PROVIDER is 'openai', but OPENAI_API_KEY is missing.")

        if self.VECTOR_DB_TYPE == "pinecone" and not self.PINECONE_API_KEY:
            raise ValueError("VECTOR_DB_TYPE is 'pinecone', but PINECONE_API_KEY is missing.")

        if self.VECTOR_DB_TYPE == "pinecone" and not self.PINECONE_EMBEDDING_MODEL:
            raise ValueError(
                "VECTOR_DB_TYPE is 'pinecone', but PINECONE_EMBEDDING_MODEL is missing."
            )

