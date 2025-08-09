#!/usr/bin/env python3
"""
An improved test suite for the cloud-native RAG system.
"""

import os
import sys
import shutil
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import Config
from document_processor import DocumentProcessor
from vector_store import VectorStore
from query_engine import QueryEngine
from models import QueryRequest

# --- Test Constants ---
SAMPLE_DOC_FILENAME = "test_agreement.txt"
SAMPLE_DOC_ID = "sample-agreement-cloud-123"
TEST_QUERY = "What severance is provided for termination without cause?"
EXPECTED_ANSWER_SNIPPET = "one month's salary"
SAMPLE_TEXT = """
EMPLOYMENT AGREEMENT
This Agreement is between Cloud Corp Inc. and Jane Smith.
SECTION 1: SEVERANCE
If terminated without cause, the Employee gets one month's salary per year of service.
"""

class SystemTests:
    """A class to encapsulate all system integration tests."""
    
    config = None
    doc_processor = None
    vector_store = None
    query_engine = None

    @classmethod
    def setup_class(cls):
        """Set up the test environment once for all tests."""
        print("\n--- Setting up cloud-native test environment ---")
        try:
            cls.config = Config()
            # Ensure tests run against Pinecone with a cloud model
            if cls.config.VECTOR_DB_TYPE != "pinecone" or not cls.config.PINECONE_EMBEDDING_MODEL:
                raise ValueError("Tests for this version must be run with VECTOR_DB_TYPE='pinecone' and a PINECONE_EMBEDDING_MODEL set in .env")

            cls.doc_processor = DocumentProcessor()
            cls.vector_store = VectorStore()
            cls.query_engine = QueryEngine(cls.vector_store)

            with open(SAMPLE_DOC_FILENAME, "w") as f:
                f.write(SAMPLE_TEXT)

            print(f"Processing sample document: {SAMPLE_DOC_FILENAME}")
            doc_result = cls.doc_processor.process_document(SAMPLE_DOC_FILENAME, SAMPLE_DOC_ID)
            cls.vector_store.add_documents(doc_result["chunks"])
            print("--- Setup complete ---")
        except Exception as e:
            print(f"--- ❌ SETUP FAILED: {e} ---")
            cls.teardown_class()
            sys.exit(1)

    @classmethod
    def teardown_class(cls):
        """Clean up the test environment after all tests are run."""
        print("\n--- Tearing down test environment ---")
        if os.path.exists(SAMPLE_DOC_FILENAME):
            os.remove(SAMPLE_DOC_FILENAME)
        
        # Clean up the test document from Pinecone
        if cls.vector_store:
            cls.vector_store.index.delete(filter={"document_id": SAMPLE_DOC_ID})
            print(f"Cleaned up test document '{SAMPLE_DOC_ID}' from Pinecone.")
        
        print("--- Teardown complete ---")

    def test_end_to_end_query(self):
        """Verifies the full RAG pipeline from query to answer."""
        print("\n🧪 Testing End-to-End Query and Retrieval...")
        
        request = QueryRequest(question=TEST_QUERY, document_ids=[SAMPLE_DOC_ID])
        response = self.query_engine.process_query(request)
        
        assert response and response.answer, "Query engine returned no answer."
        assert EXPECTED_ANSWER_SNIPPET in response.answer.lower(), \
            f"Answer did not contain expected text. Got: '{response.answer}'"
            
        print("✅ PASSED: End-to-end query returned the correct answer.")
        print(f"   Query: {TEST_QUERY}")
        print(f"   Answer: {response.answer}")

def main():
    """Main function to run the test suite."""
    print("🚀 LLM-powered Intelligent Query–Retrieval System - Cloud Model Test Suite")
    print("=" * 70)
    
    SystemTests.setup_class()
    test_suite = SystemTests()
    passed = False
    
    try:
        test_suite.test_end_to_end_query()
        passed = True
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    
    SystemTests.teardown_class()
    
    print("\n" + "=" * 70)
    if passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    main()