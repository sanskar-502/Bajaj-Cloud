# query_engine.py

import re
from typing import List, Dict, Any, Optional, Tuple
from config import Config
from models import (
    QueryResponse, ClauseInfo, LogicTree, LogicTreeType, LogicCondition,
    SearchResult, QueryRequest
)
from vector_store import VectorStore
from llm_providers import get_llm_provider, LLMProvider

class QueryEngine:
    """Handles the end-to-end process of answering user queries."""

    def __init__(self, vector_store: VectorStore):
        """
        Initializes the QueryEngine.
        - `vector_store`: An instance of a VectorStore implementation.
        """
        self.config = Config()
        self.vector_store = vector_store
        self.llm_provider: LLMProvider = get_llm_provider()
        model_name = getattr(self.llm_provider, 'model_name', 'N/A')
        print(f"[QueryEngine] Initialized with LLM Provider: {type(self.llm_provider).__name__} (Model: {model_name})")

    def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Processes a user query through the RAG pipeline and returns a structured response.
        """
        search_results = self.vector_store.search(
            query=request.question,
            top_k=request.max_results,
            document_ids=request.document_ids
        )
        
        filtered_results = [r for r in search_results if r.score >= self.config.SIMILARITY_THRESHOLD]
        
        if not filtered_results:
            return self._create_no_results_response()
            
        clauses_used = self._create_clauses_from_search(filtered_results)
        answer, confidence = self._generate_final_answer(request.question, clauses_used)
        
        logic_tree = None
        if request.include_logic:
            logic_tree = self._generate_logic_tree_with_llm(request.question, clauses_used)

        intent, entities = self._extract_intent_and_entities(request.question)

        return QueryResponse(
            answer=answer,
            clauses_used=clauses_used,
            logic_tree=logic_tree,
            confidence=confidence,
            query_intent=intent,
            entities=entities
        )

# In query_engine.py

    def _generate_final_answer(self, question: str, clauses: List[ClauseInfo]) -> Tuple[str, float]:
        """Generates a final, synthesized answer using the LLM based on the provided clauses."""
        context = "\n\n".join(
            # Providing a clause ID helps the LLM with citation
            f"Source Clause ID: {c.clause_id}\nClause Content:\n{c.text}" for c in clauses
        )
        
        # --- REFINED PROMPT FOR HACKATHON ---
        prompt = f"""
        You are a meticulous and precise Insurance Policy Analyst. Your task is to answer the user's question based *only* on the provided context from the policy document.

        **Context from Policy Document:**
        ---
        {context}
        ---

        **User's Question:** {question}

        **Instructions:**
        1.  **Analyze the Context:** Carefully read the provided clauses to find the exact answer.
        2.  **Extract Key Details:** Pay close attention to specific details such as waiting periods, monetary limits, percentages, and conditions.
        3.  **Synthesize a Factual Answer:** Formulate a direct and unambiguous answer. If possible, use the exact phrasing or quote from the document for key details.
        4.  **Cite Your Source:** If the answer is found in a specific clause, mention its ID (e.g., "According to clause...").
        5.  **Handle Missing Information:** If the information is not present in the provided context, you MUST respond with the exact phrase: "The provided documents do not contain a clear answer to this question." Do not infer or use outside knowledge.
        6.  **Confidence Score:** After your answer, on a new line, provide a confidence score from 0.0 to 1.0 based on how directly the context answers the question. Format it as: `Confidence: [score]`
        """
        
        response_text = self.llm_provider.generate_response(prompt)
        
        confidence_match = re.search(r"Confidence:\s*([0-9]*\.?[0-9]+)", response_text, re.IGNORECASE)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                # Remove the confidence line and any trailing whitespace from the answer
                answer = response_text.split(confidence_match.group(0))[0].strip()
            except ValueError:
                confidence = 0.5 # Default confidence if parsing fails
                answer = response_text.strip()
        else:
            confidence = 0.5 # Default confidence if the model forgets to include it
            answer = response_text.strip()
            
        return answer, confidence
        
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

    def _generate_logic_tree_with_llm(self, question: str, clauses: List[ClauseInfo]) -> Optional[LogicTree]:
        """Uses the LLM to create a structured logic tree based on the question and context."""
        context = "\n\n".join(f"Clause ID: {c.clause_id}\nClause Text: {c.text}" for c in clauses)
        prompt = f"Analyze the question and clauses to create a logic tree. Question: \"{question}\"\n\nClauses:\n---\n{context}\n---\n\nTask: Identify logical conditions required to answer the question. For each, determine if it is met by the clauses and cite the source clause ID. Output a single JSON object matching this Pydantic format: {{\"type\": \"AND | OR\", \"conditions\": [{{\"condition\": \"...\", \"is_met\": boolean, \"source_clause_id\": \"...\"}}]}}"
        try:
            structured_response = self.llm_provider.generate_structured_response(prompt)
            return LogicTree.model_validate(structured_response)
        except Exception as e:
            print(f"Failed to generate or parse logic tree: {e}")
            return None

    def _create_clauses_from_search(self, search_results: List[SearchResult]) -> List[ClauseInfo]:
        """Converts raw search results into structured ClauseInfo objects."""
        return [
            ClauseInfo(
                title=res.metadata.get("title", "Untitled Section"),
                text=res.content,
                document_id=res.metadata.get("document_id", "unknown"),
                page=res.metadata.get("page"),
                relevance_score=res.score,
                clause_id=res.metadata.get("id"),
            ) for res in search_results
        ]

    def _extract_intent_and_entities(self, question: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        # A simple heuristic-based intent extractor
        return "General Inquiry", {}

    def _create_no_results_response(self) -> QueryResponse:
        """Creates a standardized response for when no relevant information is found."""
        return QueryResponse(
            answer="I could not find any relevant information in the documents to answer your question.",
            clauses_used=[],
            confidence=0.0,
        )

    def validate_query(self, question: str) -> Tuple[bool, str]:
        """Performs basic validation on the user's query."""
        if not (10 < len(question.strip()) < 500):
            return False, "Query must be between 10 and 500 characters."
        return True, "Query is valid."