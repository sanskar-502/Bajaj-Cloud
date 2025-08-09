# 🧠 LLM-powered Intelligent Query–Retrieval System (Cloud-Native)

[](https://www.python.org/downloads/)
[](https://opensource.org/licenses/MIT)
[](https://fastapi.tiangolo.com/)

An intelligent document analyst assistant designed to process and understand complex legal, insurance, HR, and compliance documents. The system answers user questions based on deep semantic understanding, clause relevance, and AI-generated logical reasoning.

This version is architected to use a **cloud-based embedding model**, offloading heavy computation for increased speed and accuracy.

-----

## 🎯 System Overview

This system provides a complete Retrieval- Augmented Generation (RAG) pipeline:

  - **Cloud-Native Embeddings**: Uses high-performance, hosted embedding models (e.g., `llama-text-embed-v2`) via Pinecone for state-of-the-art accuracy and speed.
  - **Multi-LLM Support**: Integrates with both **Google Gemini** and **OpenAI** models for the final answer generation.
  - **Advanced RAG**: Goes beyond simple Q\&A to provide answers with supporting evidence and a traceable reasoning process.
  - **Developer-Friendly API**: Built with **FastAPI**, offering a clean, modern REST API with automatic interactive documentation.

-----

## ✨ Features

  - **Robust Document Processing**: Supports **PDF, DOCX, TXT, and PPTX** formats.
  - **Advanced Text Extraction**: Includes **Optical Character Recognition (OCR)** to extract text even from scanned, image-based PDFs.
  - **Intelligent Chunking**: Splits documents into meaningful, overlapping chunks to preserve context.
  - **AI-Generated Reasoning**: Provides a `logic_tree` in responses to show how the AI arrived at an answer.
  - **Full API Control**: Manage the entire document lifecycle (upload, query, list, delete) through REST API endpoints.

-----

## 🛠️ Technology Stack

  - **Backend Framework**: FastAPI
  - **LLM Providers**: Google Gemini, OpenAI
  - **Vector Database**: Pinecone
  - **Cloud Embedding Models**: Pinecone Integrated Models (e.g., `llama-text-embed-v2`)
  - **Document Parsing**: PyMuPDF, python-docx, python-pptx
  - **OCR Engine**: Tesseract & Poppler
  - **Data Validation**: Pydantic

-----

## 🚀 Getting Started

This guide provides a complete roadmap for setting up and running the project.

### Step 1: System-Level Dependencies

Before setting up the Python environment, you must install the programs that the OCR features depend on.

  * **Tesseract-OCR** (for reading text from images)

      * **Windows:** Download and run the installer from **[Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)**. **Important:** During installation, make sure to check the box to "Add Tesseract to your system PATH."
      * **macOS:** `brew install tesseract`
      * **Linux (Ubuntu/Debian):** `sudo apt-get update && sudo apt-get install tesseract-ocr`

  * **Poppler** (for converting PDF pages into images for OCR)

      * **Windows:** Download the latest binary from [this link](https://github.com/oschwartz10612/poppler-windows/releases/), unzip it to a permanent location (e.g., `C:\poppler`), and add its `bin` folder to your system PATH.
      * **macOS:** `brew install poppler`
      * **Linux (Ubuntu/Debian):** `sudo apt-get install poppler-utils`

### Step 2: Python Environment Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd intelligent-query-retrieval-system-cloud
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the virtual environment
    python -m venv venv
    # Activate it (Windows)
    .\venv\Scripts\Activate.ps1
    # Activate it (macOS/Linux)
    # source venv/bin/activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy the example file to create your own local configuration.

    ```bash
    cp env_example.txt .env
    ```

    Now, **edit the `.env` file** with your secret API keys.

### Step 3: Run the Application

You are now ready to start the server.

```bash
python main.py
```

The API will start at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

-----

## ⚙️ Configuration (`.env`)

Your `.env` file is the central place for configuration.

| Variable | Description | Example Values |
| :--- | :--- | :--- |
| **`LLM_PROVIDER`** | The main switch for your Language Model. | `gemini` or `openai` |
| **`GEMINI_API_KEY`** | Your secret API key for Google's Gemini. | `AIzaSy...` |
| **`PINECONE_API_KEY`** | Your secret API key for Pinecone. | `pcsk_...` |
| **`PINECONE_INDEX_NAME`**| The name of your index in Pinecone. | `cloud-model-index` |
| **`PINECONE_EMBEDDING_MODEL`**| The cloud-hosted model to use. | `llama-text-embed-v2` |
| **`SIMILARITY_THRESHOLD`** | The minimum score for a chunk to be relevant. | `0.5` (Balanced), `0.6` (Stricter) |

-----

## 🔌 API Endpoints

Visit `http://127.0.0.1:8000/docs` for a full interactive API specification.

  - `POST /upload`: Upload a document for processing.
  - `POST /query`: Ask a question about the processed documents.
  - `POST /hackrx/run`: Special endpoint for the hackathon submission.

-----

## 🚨 Troubleshooting

  - **Configuration Error on Startup**: Check your `.env` file. Ensure the required keys for your selected `LLM_PROVIDER` and `PINECONE_EMBEDDING_MODEL` are present and correct.
  - **`ModuleNotFoundError`**: Make sure your virtual environment is activated and you have run `pip install -r requirements.txt`.
  - **OCR Errors (`tesseract` or `poppler` not found)**: This means a system-level dependency is missing or not in your PATH. Close your terminals, reinstall the program, and ensure you add it to your system's PATH.
  - **Check `app.log`**: For any other issues, the `app.log` file will contain detailed error messages.