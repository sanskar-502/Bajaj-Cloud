import os
import shutil
import uuid

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, UploadFile

from policymind.dependencies.container import AppContainer
from policymind.models.schemas import (
    QueryRequest,
    QueryResponse,
    SubmissionRequest,
    SubmissionResponse,
    UploadResponse,
)


router = APIRouter()


def get_container() -> AppContainer:
    # Import inside dependency to avoid circular app imports.
    from policymind.app import get_container_from_app

    return get_container_from_app()


async def process_and_cleanup_document(
    file_path: str, document_id: str, container: AppContainer
) -> None:
    try:
        result = container.document_processor.process_document(file_path, document_id)
        container.vector_store.add_documents(result["chunks"])
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/", summary="Root endpoint")
async def root() -> dict[str, str]:
    return {"message": "PolicyMind API"}


@router.post("/upload", response_model=UploadResponse, summary="Upload a document for querying")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    container: AppContainer = Depends(get_container),
) -> UploadResponse:
    settings = container.settings
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: '{ext}'.")
    if file.size and file.size > settings.MAX_FILE_SIZE * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {settings.MAX_FILE_SIZE}MB.")

    document_id = f"{uuid.uuid4()}{ext}"
    temp_path = os.path.join(settings.UPLOAD_DIR, document_id)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(process_and_cleanup_document, temp_path, document_id, container)
    return UploadResponse(
        success=True,
        document_id=document_id,
        message="Document uploaded successfully. Processing in the background.",
    )


@router.post("/query", response_model=QueryResponse, summary="Ask a question about uploaded documents")
async def query_documents(
    request: QueryRequest, container: AppContainer = Depends(get_container)
) -> QueryResponse:
    is_valid, message = container.query_engine.validate_query(request.question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return container.query_engine.process_query(request)


@router.post("/hackrx/run", response_model=SubmissionResponse, summary="Run a submission for hackathon")
async def run_submission(
    request: SubmissionRequest,
    authorization: str = Header(None),
    container: AppContainer = Depends(get_container),
) -> SubmissionResponse:
    settings = container.settings
    if not authorization or authorization.split(" ")[-1] != settings.HACKRX_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    temp_file_path = None
    temp_doc_id = f"hackathon-{uuid.uuid4()}.pdf"
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                request.documents, headers=headers, follow_redirects=True, timeout=60.0
            )
            response.raise_for_status()
            file_content = response.content

        temp_file_path = os.path.join(settings.UPLOAD_DIR, temp_doc_id)
        with open(temp_file_path, "wb") as file_handle:
            file_handle.write(file_content)

        doc_data = container.document_processor.process_document(temp_file_path, temp_doc_id)
        container.vector_store.add_documents(doc_data["chunks"])

        answers = []
        for question in request.questions:
            query_request = QueryRequest(
                question=question, document_ids=[temp_doc_id], include_logic=False
            )
            query_result = container.query_engine.process_query(query_request)
            answers.append(query_result.answer)
        return SubmissionResponse(answers=answers)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {exc}") from exc
    finally:
        container.vector_store.delete_documents(document_ids=[temp_doc_id])
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

