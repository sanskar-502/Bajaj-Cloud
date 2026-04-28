# PolicyMind

PolicyMind is a cloud-first Retrieval-Augmented Generation (RAG) API for document intelligence.  
It ingests policy and compliance documents, extracts and chunks text, indexes semantic records in Pinecone with integrated embeddings, and returns grounded, evidence-aware answers.

This repository is structured for production readability with clear separation of API, configuration, service logic, schemas, and dependency wiring.

---

## 1) What PolicyMind Does

PolicyMind supports:

- Multi-format document ingestion: PDF, DOCX, TXT, PPTX
- OCR fallback for scanned PDFs (Tesseract + Poppler)
- Semantic indexing using Pinecone integrated embedding models
- Question answering over indexed content
- Optional reasoning tree in responses (`logic_tree`)
- Temporary isolated processing flow for hackathon submission endpoint

Typical use cases:

- Insurance policy query answering
- Legal/compliance clause discovery
- HR policy verification
- Internal knowledge retrieval from large unstructured documents

---

## 2) Core Features

- **Cloud-native vector workflow**  
  Uses Pinecone integrated embedding model (`PINECONE_EMBEDDING_MODEL`) so embedding generation is handled natively by Pinecone.

- **Asynchronous LLM Orchestration**  
  Built with fully asynchronous I/O (`AsyncOpenAI` & `google-generativeai`) to eliminate thread-blocking during high-latency RAG tasks.

- **Enterprise Resiliency**  
  Implements strict dependency injection, static type checking (`mypy`), and exponential-backoff retry logic (`tenacity`) to gracefully handle LLM rate limits.

- **Document lifecycle API**  
  Upload, process, query, and temporary isolated processing for external evaluation flows.

- **Structured responses**  
  Returns relevant clauses, confidence score, and optional logic-tree object.

- **Production-friendly code organization**  
  Clean package layout under `src/policymind` with app factory and dependency container.

---

## 3) Project Structure

```text
PolicyMind/
├── src/
│   └── policymind/
│       ├── app.py                     # FastAPI app factory + startup hooks
│       ├── main.py                    # Runtime launcher logic
│       ├── api/
│       │   └── routes.py              # Route handlers
│       ├── core/
│       │   ├── config.py              # Settings and env validation
│       │   └── logging.py             # Logging setup
│       ├── dependencies/
│       │   └── container.py           # Dependency container wiring
│       ├── models/
│       │   └── schemas.py             # Pydantic request/response models
│       └── services/
│           ├── document_processor.py  # Parsing, OCR, chunking
│           ├── llm_providers.py       # Gemini/OpenAI adapters
│           ├── query_engine.py        # RAG query orchestration
│           └── vector_store.py        # Pinecone data operations
├── tests/
│   ├── unit/
│   │   └── test_query_engine.py       # Async mocking & Pydantic validation tests
│   └── test_smoke.py                  # Basic import/smoke scaffold
├── .github/
│   └── workflows/
│       └── ci.yml                     # CI/CD Pipeline (Ruff, MyPy, Pytest)
├── Dockerfile                         # Production container definition
├── docker-compose.yml                 # Local container orchestration
├── requirements.txt
├── .env.example
├── .gitignore
└── main.py                            # Root compatibility launcher
```

---

## 4) End-to-End Processing Flow

### Upload and Index Flow (`POST /upload`)

1. Validate extension and file size.
2. Save uploaded file to `UPLOAD_DIR`.
3. Background task starts processing:
   - Extract text from document.
   - If PDF text extraction is weak, fallback to OCR.
   - Clean text and split into semantic chunks.
   - Build records with metadata (`document_id`, `chunk_id`, `document_type`).
4. Upsert records into Pinecone namespace.
5. Cleanup temporary file.

### Query Flow (`POST /query`)

1. Validate question length.
2. Search Pinecone with raw query text.
3. Filter by similarity threshold.
4. Build clause objects from top hits.
5. Generate final answer with LLM using clause context.
6. Parse confidence from model output.
7. Optionally request structured `logic_tree`.

### Hackathon Flow (`POST /hackrx/run`)

1. Validate bearer token (`HACKRX_TOKEN`).
2. Download document from URL.
3. Process + index document temporarily.
4. Answer all provided questions with `document_ids=[temp_doc_id]`.
5. Delete temporary vectors and local file.

---

## 5) Technology Stack

- **Web/API**: FastAPI, Uvicorn
- **Vector DB**: Pinecone (`pinecone`)
- **LLM providers**: Google Gemini (`google-generativeai`), OpenAI (`openai`)
- **Document extraction**: PyMuPDF, PyPDF2, python-docx, python-pptx
- **OCR**: pytesseract + pdf2image
- **Validation/Resiliency**: Pydantic, mypy, tenacity
- **Orchestration**: Docker, GitHub Actions, docker-compose
- **Utilities**: nltk, python-dotenv, httpx, numpy

---

## 6) Prerequisites

### System prerequisites

- Python 3.10+ (recommended: 3.11/3.12)
- Tesseract OCR installed and available in PATH
- Poppler installed and available in PATH

Windows:

1. Install Tesseract (UB Mannheim build recommended).
2. Install Poppler binaries and add `bin` to PATH.
3. Restart terminal after PATH changes.

macOS:

```bash
brew install tesseract poppler
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

---

## 7) Local Setup (Step-by-Step)

### Step 1: Clone & Configure

```bash
git clone https://github.com/sanskar-502/Bajaj-Cloud.git
cd PolicyMind
cp .env.example .env # Add your Pinecone/OpenAI keys
```

### Option A: Run via Docker (Recommended for Production)

```bash
docker-compose up -d --build
```
*API will run at `http://127.0.0.1:8000`*

### Option B: Local Development (Manual Setup)

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1 # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
uvicorn policymind.app:app --reload
```

Server:

- API: `http://127.0.0.1:8000`
- Docs (Swagger): `http://127.0.0.1:8000/docs`

---

## 8) Environment Variables

Use `.env.example` as base.

### LLM settings

- `LLM_PROVIDER`: `gemini` or `openai`
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

### Vector settings

- `VECTOR_DB_TYPE` (default: `pinecone`)
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_EMBEDDING_MODEL` (default: `llama-text-embed-v2`)
- `EMBEDDING_MODEL` (kept for compatibility/fallback references)

### Retrieval/chunking

- `CHUNK_SIZE` (default: `1000`)
- `CHUNK_OVERLAP` (default: `200`)
- `TOP_K_RESULTS` (default: `5`)
- `SIMILARITY_THRESHOLD` (default: `0.5`)
- `MAX_FILE_SIZE` in MB (default: `50`)

### Server/runtime

- `API_HOST` (default: `0.0.0.0`)
- `API_PORT` (default: `8000`)
- `UPLOAD_DIR` (default: `uploads`)
- `VECTOR_STORE_DIR` (legacy compatibility)
- `LOG_LEVEL` (default: `INFO`)
- `HACKRX_TOKEN` (auth token for `/hackrx/run`)

---

## 9) API Reference

### `GET /`

Basic health/info response.

### `POST /upload`

Uploads one document for background processing.

Request: multipart/form-data

- `file`: document file

Response:

- `success`
- `document_id`
- `message`

### `POST /query`

Ask a question over indexed docs.

Request JSON example:

```json
{
  "question": "What is the waiting period for pre-existing diseases?",
  "document_ids": ["<doc-id-1>", "<doc-id-2>"],
  "include_logic": true,
  "max_results": 5
}
```

Response includes:

- `answer`
- `clauses_used[]`
- `logic_tree` (optional)
- `confidence`
- `query_intent`
- `entities`

### `POST /hackrx/run`

Runs isolated processing over an external document URL and returns answers for all questions.

Headers:

- `Authorization: Bearer <HACKRX_TOKEN>`

Request JSON example:

```json
{
  "documents": "https://example.com/policy.pdf",
  "questions": [
    "What is the room rent limit?",
    "Is maternity covered and after what waiting period?"
  ]
}
```

Response:

```json
{
  "answers": ["...", "..."]
}
```

---

## 10) Startup and Runtime Notes

- App uses startup event to build dependency container.
- Services are constructed once and reused.
- Upload processing is offloaded to FastAPI background tasks.
- Logs are written to `app.log` and stdout.
- Temporary files are cleaned after processing.
- Hackathon flow removes temporary vectors after answer generation.

---

## 11) Development and Testing

### Smoke test scaffold

```bash
pytest -q
```

Current test includes basic app import/creation sanity check with mocked container setup.

### Useful checks

```bash
python -m compileall src/policymind
```

---

## 12) Troubleshooting

- **Missing dependency errors (`docx`, `python-multipart`, etc.)**  
  Activate the correct virtualenv and run `pip install -r requirements.txt`.

- **401 on `/hackrx/run`**  
  Verify `Authorization` header format and `HACKRX_TOKEN`.

- **Pinecone connection/index errors**  
  Check `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, network access, and project quotas.

- **No relevant answers / low confidence**  
  Tune `SIMILARITY_THRESHOLD`, `TOP_K_RESULTS`, `CHUNK_SIZE`, and `CHUNK_OVERLAP`.

- **OCR not working**  
  Confirm Tesseract and Poppler are installed and visible in PATH.

- **Slow PDF processing**  
  Scanned PDFs trigger OCR; this is expected to be slower.

---

## 13) Security and Operational Guidance

- Never commit `.env` or API keys.
- Use a strong non-default `HACKRX_TOKEN`.
- Restrict CORS origins in production.
- Add API gateway/rate limits in internet-facing deployments.
- Keep Pinecone index names environment-specific (`dev`, `staging`, `prod`).

---

## 14) Backward Compatibility

Root-level compatibility modules are present to prevent breaking older imports/scripts while using the new `src/policymind` structure.

---

## 15) License

Internal/hackathon use unless a separate license file is added.
# PolicyMind

PolicyMind is a production-structured FastAPI RAG service for insurance and policy document Q&A.  
It processes uploaded documents, indexes content in Pinecone with integrated embeddings, and answers questions with evidence-backed responses.

## Architecture

- `src/policymind/app.py`: app factory and startup wiring
- `src/policymind/api/routes.py`: HTTP route handlers
- `src/policymind/core/`: config and logging
- `src/policymind/services/`: document processing, vector storage, query engine, LLM providers
- `src/policymind/models/schemas.py`: API/data schemas
- `src/policymind/dependencies/container.py`: dependency container

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env` (see `.env.example`).
4. Run the app:

```bash
python main.py
```

## API Endpoints

- `GET /` health/info
- `POST /upload` upload document for indexing
- `POST /query` ask questions against indexed documents
- `POST /hackrx/run` run isolated hackathon document flow

Interactive docs: `http://127.0.0.1:8000/docs`

## Notes

- Cloud-first vector flow uses Pinecone integrated embeddings (`PINECONE_EMBEDDING_MODEL`).
- OCR requires Tesseract and Poppler to be installed on the machine.