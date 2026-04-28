import pytest
from unittest.mock import AsyncMock, MagicMock
from policymind.services.query_engine import QueryEngine
from policymind.models.schemas import QueryRequest, SearchResult, ClauseInfo


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.SIMILARITY_THRESHOLD = 0.7
    return settings


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.search.return_value = [
        SearchResult(content="Policy covers fire damage.", score=0.85, metadata={}),
    ]
    return store


@pytest.fixture
def mock_llm_provider():
    provider = AsyncMock()
    provider.generate_response.return_value = "Yes, fire damage is covered. Confidence: 0.95"
    provider.generate_structured_response.return_value = {
        "type": "AND",
        "conditions": [{"condition": "Fire damage", "is_met": True, "source_clause_id": "1"}]
    }
    return provider


@pytest.mark.asyncio
async def test_process_query_success(mock_settings, mock_vector_store, mock_llm_provider):
    # Ensure query engine allows asynchronous LLM provider
    engine = QueryEngine(settings=mock_settings, vector_store=mock_vector_store, llm_provider=mock_llm_provider)

    # Mock inner method that processes search to clauses since it's synchronous
    engine._create_clauses_from_search = MagicMock(return_value=[ClauseInfo(
        clause_id="1", 
        text="Policy covers fire damage.", 
        source_document_id="doc1",
        title="Fire Damage Clause",
        document_id="doc1",
        relevance_score=0.9
    )])
    engine._extract_intent_and_entities = MagicMock(return_value=("Information Retrieval", {}))

    request = QueryRequest(question="Is fire damage covered?", max_results=3, include_logic=True)
    
    response = await engine.process_query(request)

    assert response.confidence == 0.95
    assert "fire damage is covered" in response.answer.lower()
    assert response.logic_tree is not None
    assert response.logic_tree.type == "AND"

