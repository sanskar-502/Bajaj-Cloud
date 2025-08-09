import os
import shutil
import uuid
from typing import List, Optional

import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from models import (
    QueryRequest, QueryResponse, UploadResponse, SubmissionRequest, SubmissionResponse,
)
from document_processor import DocumentProcessor
from vector_store import VectorStore
from query_engine import QueryEngine

# --- Initialization ---
app = FastAPI(title="LLM-powered Intelligent Query–Retrieval System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Instances (Created once on startup) ---
config = Config()
document_processor = DocumentProcessor()
vector_store = VectorStore()
query_engine = QueryEngine(vector_store)

EXPECTED_TOKEN = "a9710e8faf1eb0aa73caf8530b1bcac6889870fb4e3ef80e8bc17f380a3a83bc"
os.makedirs(config.UPLOAD_DIR, exist_ok=True)

# --- Background Task for General Uploads ---
async def process_and_cleanup_document(file_path: str, document_id: str):
    """Processes a document and adds it to the main vector store."""
    try:
        print(f"Background processing started for document_id: {document_id}")
        result = document_processor.process_document(file_path, document_id)
        vector_store.add_documents(result["chunks"])
        print(f"✅ Successfully processed and indexed document_id: {document_id}")
    except Exception as e:
        print(f"❌ Error processing document {document_id}: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# --- General API Endpoints ---
@app.get("/", summary="Root endpoint")
async def root():
    return {"message": "LLM-powered Intelligent Query–Retrieval System"}

@app.post("/upload", response_model=UploadResponse, summary="Upload a document for querying")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in config.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: '{ext}'.")
    if file.size > config.MAX_FILE_SIZE * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {config.MAX_FILE_SIZE}MB.")
    try:
        document_id = f"{uuid.uuid4()}{ext}"
        temp_path = os.path.join(config.UPLOAD_DIR, document_id)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        background_tasks.add_task(process_and_cleanup_document, temp_path, document_id)
        return UploadResponse(
            success=True,
            document_id=document_id,
            message="Document uploaded successfully. Processing in the background."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/query", response_model=QueryResponse, summary="Ask a question about uploaded documents")
async def query_documents(request: QueryRequest):
    is_valid, message = query_engine.validate_query(request.question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return query_engine.process_query(request)

# --- HACKATHON SUBMISSION ENDPOINT (CORRECTED LOGIC) ---
@app.post("/hackrx/run", response_model=SubmissionResponse, summary="Run a submission for the hackathon")
async def run_submission(
    request: SubmissionRequest,
    authorization: str = Header(None)
):
    """
    Performs the RAG pipeline on-the-fly for a specific document without
    polluting the main vector index, and reuses global components for stability.
    """
    if not authorization or authorization.split(" ")[1] != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    temp_file_path = None
    # Use a unique ID for this specific hackathon run to isolate it
    temp_doc_id = f"hackathon-{uuid.uuid4()}.pdf"
    try:
        # 1. Download the document
        # FIX: Add a browser-like User-Agent header to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                request.documents,
                headers=headers,
                follow_redirects=True,
                timeout=60.0
            )
            response.raise_for_status()
            file_content = response.content

        temp_file_path = os.path.join(config.UPLOAD_DIR, temp_doc_id)
        with open(temp_file_path, "wb") as f:
            f.write(file_content)

        # 2. Process and add document to the main Pinecone index
        doc_data = document_processor.process_document(temp_file_path, temp_doc_id)
        vector_store.add_documents(doc_data["chunks"]) # Use the global vector_store

        # 3. Answer questions using the global query engine
        answers = []
        for question in request.questions:
            query_req = QueryRequest(
                question=question,
                document_ids=[temp_doc_id], # CRITICAL: Isolate the search to this document
                include_logic=False
            )
            # REUSE the global query_engine instance for stability and efficiency
            query_res = query_engine.process_query(query_req)
            answers.append(query_res.answer)
            
        print(f"✅ Successfully answered {len(answers)} questions for document {temp_doc_id}.")
        return SubmissionResponse(answers=answers)
    
    except httpx.RequestError as e:
        # This will now catch the 4xx/5xx errors from the download attempt
        raise HTTPException(status_code=400, detail=f"Failed to download document: {e}")
    except Exception as e:
        print(f"❌ An error occurred during hackathon processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {str(e)}")
    finally:
        # 4. Cleanup: Ensure the temporary document is removed from Pinecone and local disk
        if vector_store and temp_doc_id:
            print(f"Cleaning up temporary document {temp_doc_id} from Pinecone...")
            vector_store.delete_documents(document_ids=[temp_doc_id])
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)