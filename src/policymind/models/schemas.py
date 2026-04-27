from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    INSURANCE_POLICY = "insurance_policy"
    LEGAL_CONTRACT = "legal_contract"
    HR_POLICY = "hr_policy"
    COMPLIANCE_DOC = "compliance_doc"
    UNKNOWN = "unknown"


class LogicTreeType(str, Enum):
    AND = "AND"
    OR = "OR"
    CONDITIONAL = "CONDITIONAL"


class ClauseInfo(BaseModel):
    title: str = Field(description="Title or name of the clause/section.")
    text: str = Field(description="The full text content of the clause.")
    document_id: str = Field(description="The unique ID of the source document.")
    relevance_score: float = Field(
        description="Relevance score (0.0 to 1.0) of the clause to the query.", ge=0.0, le=1.0
    )
    page: Optional[int] = Field(None, description="Page number where the clause appears.")
    clause_id: Optional[str] = Field(None, description="A unique identifier for this clause.")


class LogicCondition(BaseModel):
    condition: str = Field(description="A human-readable description of the condition.")
    is_met: bool = Field(description="Whether the condition is met based on evidence.")
    source_clause_id: Optional[str] = Field(None, description="Source clause identifier.")


class LogicTree(BaseModel):
    type: LogicTreeType = Field(description="Logical operation for this node.")
    conditions: List[Union["LogicCondition", "LogicTree"]] = Field(
        description="List of conditions or nested logic trees."
    )
    result: Optional[bool] = Field(None, description="Evaluated result of this logic node.")


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    include_logic: bool = True
    max_results: int = 5


class QueryResponse(BaseModel):
    answer: str
    clauses_used: List[ClauseInfo]
    logic_tree: Optional[LogicTree] = None
    confidence: float = Field(ge=0.0, le=1.0)
    query_intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    success: bool
    document_id: str
    message: str


class SubmissionRequest(BaseModel):
    documents: str
    questions: List[str]


class SubmissionResponse(BaseModel):
    answers: List[str]


class DocumentMetadata(BaseModel):
    document_id: str
    document_type: DocumentType
    upload_timestamp: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    company_name: Optional[str] = None


class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float


class ErrorResponse(BaseModel):
    error: str = Field(description="A high-level description of the error.")
    details: Optional[str] = Field(None, description="Additional debugging details.")
    error_code: Optional[str] = Field(None, description="Optional internal error code.")


LogicTree.model_rebuild()

