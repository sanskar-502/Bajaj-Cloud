# models.py

"""
Pydantic Data Models
Defines the data structures and contracts for the API and internal components.
Pydantic ensures data validation, serialization, and generates OpenAPI schemas.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# --- Enumerations for controlled vocabularies ---

class DocumentType(str, Enum):
    """Enumeration for the types of documents the system can classify."""
    INSURANCE_POLICY = "insurance_policy"
    LEGAL_CONTRACT = "legal_contract"
    HR_POLICY = "hr_policy"
    COMPLIANCE_DOC = "compliance_doc"
    UNKNOWN = "unknown"


class LogicTreeType(str, Enum):
    """Enumeration for the types of logical operations in the reasoning tree."""
    AND = "AND"
    OR = "OR"
    CONDITIONAL = "CONDITIONAL"


# --- Core Data Structures for Reasoning and Content ---

class ClauseInfo(BaseModel):
    """Represents a relevant clause or section retrieved from a document."""
    title: str = Field(description="Title or name of the clause/section.")
    text: str = Field(description="The full text content of the clause.")
    document_id: str = Field(description="The unique ID of the source document.")
    relevance_score: float = Field(description="Relevance score (0.0 to 1.0) of the clause to the query.", ge=0.0, le=1.0)
    page: Optional[int] = Field(None, description="Page number where the clause appears, if applicable.")
    clause_id: Optional[str] = Field(None, description="A unique identifier for this specific clause.")


class LogicCondition(BaseModel):
    """Represents a single condition within the reasoning logic tree."""
    condition: str = Field(description="A human-readable description of the logical condition.")
    is_met: bool = Field(description="Indicates whether the condition is met based on the evidence.")
    source_clause_id: Optional[str] = Field(None, description="The ID of the clause providing evidence for this condition.")


class LogicTree(BaseModel):
    """A recursive structure representing the logical reasoning process of the LLM."""
    type: LogicTreeType = Field(description="The logical operation for this node (e.g., AND, OR).")
    conditions: List[Union['LogicCondition', 'LogicTree']] = Field(description="List of conditions or nested logic trees.")
    result: Optional[bool] = Field(None, description="The evaluated boolean result of this logic node.")


# --- API Request and Response Models ---

class QueryRequest(BaseModel):
    """Defines the structure for a user's query request."""
    question: str
    document_ids: Optional[List[str]] = None
    include_logic: bool = True
    max_results: int = 5

class QueryResponse(BaseModel):
    """Defines the structured response returned for a successful query."""
    answer: str
    clauses_used: List[ClauseInfo]
    logic_tree: Optional[LogicTree] = None
    confidence: float = Field(ge=0.0, le=1.0)
    query_intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    """Defines the response after a document is submitted for background processing."""
    success: bool
    document_id: str
    message: str

class SubmissionRequest(BaseModel):
    """Defines the request body for the hackathon submission endpoint."""
    documents: str
    questions: List[str]

class SubmissionResponse(BaseModel):
    """Defines the response body for the hackathon submission endpoint."""
    answers: List[str]

# --- Internal and Utility Models ---

class DocumentMetadata(BaseModel):
    """Represents the metadata associated with a single processed document."""
    document_id: str
    document_type: DocumentType
    upload_timestamp: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    company_name: Optional[str] = None

class SearchResult(BaseModel):
    """Represents a single raw search result from the vector store."""
    content: str
    metadata: Dict[str, Any]
    score: float

class ErrorResponse(BaseModel):
    """A standardized format for returning errors from the API."""
    error: str = Field(description="A high-level description of the error.")
    details: Optional[str] = Field(None, description="Additional details about the error for debugging.")
    error_code: Optional[str] = Field(None, description="An optional internal error code.")


# This command resolves the forward reference in the LogicTree model,
# allowing it to refer to itself for recursive structures.
LogicTree.model_rebuild()