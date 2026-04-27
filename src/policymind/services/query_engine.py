import re
from typing import Any, Dict, List, Optional, Tuple

from policymind.core.config import Settings
from policymind.models.schemas import (
    ClauseInfo,
    LogicTree,
    QueryRequest,
    QueryResponse,
    SearchResult,
)
from policymind.services.llm_providers import LLMProvider
from policymind.services.vector_store import VectorStore


class QueryEngine:
    def __init__(self, settings: Settings, vector_store: VectorStore, llm_provider: LLMProvider):
        self.settings = settings
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    def process_query(self, request: QueryRequest) -> QueryResponse:
        search_results = self.vector_store.search(
            query=request.question,
            top_k=request.max_results,
            document_ids=request.document_ids,
        )
        filtered_results = [
            result for result in search_results if result.score >= self.settings.SIMILARITY_THRESHOLD
        ]
        if not filtered_results:
            return self._create_no_results_response()

        clauses_used = self._create_clauses_from_search(filtered_results)
        answer, confidence = self._generate_final_answer(request.question, clauses_used)
        logic_tree: Optional[LogicTree] = None
        if request.include_logic:
            logic_tree = self._generate_logic_tree_with_llm(request.question, clauses_used)
        intent, entities = self._extract_intent_and_entities(request.question)
        return QueryResponse(
            answer=answer,
            clauses_used=clauses_used,
            logic_tree=logic_tree,
            confidence=confidence,
            query_intent=intent,
            entities=entities,
        )

    def _generate_final_answer(self, question: str, clauses: List[ClauseInfo]) -> Tuple[str, float]:
        context = "\n\n".join(
            f"Source Clause ID: {clause.clause_id}\nClause Content:\n{clause.text}"
            for clause in clauses
        )
        prompt = f"""
        You are a meticulous and precise Insurance Policy Analyst. Your task is to answer the user's question based *only* on the provided context from the policy document.

        **Context from Policy Document:**
        ---
        {context}
        ---

        **User's Question:** {question}

        **Instructions:**
        1. Analyze the context and extract concrete details.
        2. Synthesize a direct answer using document evidence only.
        3. If missing, respond exactly: "The provided documents do not contain a clear answer to this question."
        4. End with: Confidence: [score from 0.0 to 1.0]
        """
        response_text = self.llm_provider.generate_response(prompt)
        confidence_match = re.search(r"Confidence:\s*([0-9]*\.?[0-9]+)", response_text, re.IGNORECASE)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                answer = response_text.split(confidence_match.group(0))[0].strip()
            except ValueError:
                confidence = 0.5
                answer = response_text.strip()
        else:
            confidence = 0.5
            answer = response_text.strip()
        return answer, confidence

    def _generate_logic_tree_with_llm(
        self, question: str, clauses: List[ClauseInfo]
    ) -> Optional[LogicTree]:
        context = "\n\n".join(f"Clause ID: {clause.clause_id}\nClause Text: {clause.text}" for clause in clauses)
        prompt = (
            f'Analyze the question and clauses to create a logic tree. Question: "{question}"\n\n'
            f'Clauses:\n---\n{context}\n---\n\n'
            'Output JSON object matching: {"type":"AND | OR","conditions":[{"condition":"...","is_met":true,"source_clause_id":"..."}]}'
        )
        try:
            structured_response = self.llm_provider.generate_structured_response(prompt)
            return LogicTree.model_validate(structured_response)
        except Exception:
            return None

    def _create_clauses_from_search(self, search_results: List[SearchResult]) -> List[ClauseInfo]:
        return [
            ClauseInfo(
                title=result.metadata.get("title", "Untitled Section"),
                text=result.content,
                document_id=result.metadata.get("document_id", "unknown"),
                page=result.metadata.get("page"),
                relevance_score=result.score,
                clause_id=str(result.metadata.get("id", result.metadata.get("chunk_id", ""))),
            )
            for result in search_results
        ]

    def _extract_intent_and_entities(self, question: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        return "General Inquiry", {}

    def _create_no_results_response(self) -> QueryResponse:
        return QueryResponse(
            answer="I could not find any relevant information in the documents to answer your question.",
            clauses_used=[],
            confidence=0.0,
        )

    def validate_query(self, question: str) -> Tuple[bool, str]:
        if not (10 < len(question.strip()) < 500):
            return False, "Query must be between 10 and 500 characters."
        return True, "Query is valid."

