# DocuLens AI

DocuLens AI is an offline-first document intelligence platform for scanned financial documents. The project is being built incrementally for the ARCIL document extraction assignment.

## Current milestone: Phase 11

The project currently includes:

- React, Vite, JavaScript, Tailwind CSS, React Router, and Axios frontend
- FastAPI backend with environment-based settings and CORS
- `GET /health` connectivity check
- A dashboard that reports the live backend status
- PostgreSQL persistence through SQLAlchemy ORM
- Secure, streamed PDF uploads with MIME, extension, signature, and size validation
- UUID-based local filenames and cleanup on failed uploads
- Drag-and-drop upload UI with progress and useful error states
- Background PDF page conversion with PyMuPDF
- Ordered page-level PostgreSQL records with image dimensions
- UUID-scoped local page images and API delivery paths
- Automatic conversion status polling and a responsive page thumbnail grid
- Configurable OpenCV preprocessing with grayscale conversion, CLAHE contrast enhancement, mild denoising, adaptive thresholding, resizing, and guarded deskewing
- Separate preservation and delivery of original and preprocessed page images
- Original/preprocessed comparison control in the frontend page gallery
- Local PaddleOCR processing with one shared, lazily loaded CPU engine
- Page-level raw and cleaned OCR text, average confidence, and region bounding boxes
- Persistent OCR regions in PostgreSQL and a page-by-page inspection screen
- Visible OCR status and per-page processing progress
- Local spaCy named-entity recognition combined with financial-document regex extractors
- Persistent names, organizations, locations, dates, monetary values, account identifiers, PAN, GSTIN, IFSC, email, phone, percentage, and PIN-code results
- Document-wide and page-level entity panels with source-page traceability
- A polished three-panel document workspace with a scrollable page rail, focused page preview, and tabbed insights
- In-workspace previous/next navigation, original/enhanced image switching, OCR confidence, live processing state, and document metadata
- Scale-aware OCR bounding-box overlays aligned to the enhanced page image
- Hover and keyboard-focus OCR tooltips showing region text and confidence
- Clickable entity cards that navigate to and highlight their source region where coordinates are available
- Page-aware overlapping text chunks persisted with FAISS vector positions
- Offline `all-MiniLM-L6-v2` sentence embeddings and per-document cosine-similarity indexes
- Ranked semantic search results with scores, excerpts, page references, and click-to-page navigation
- In-memory JSON exports containing document metadata, page OCR, OCR regions, entities, and search chunks
- Excel-friendly CSV entity exports with document and source-page traceability
- Readable plain-text exports containing page-by-page OCR and an extracted-entity appendix
- Workspace export controls that download completed documents without leaving derivative files on the server
- Alembic-managed PostgreSQL schema with a tested baseline and incremental hardening migration
- Database-level cascade deletion across pages, OCR blocks, entities, and search chunks
- Indexed document creation and document-scoped entity ordering for common lookups
- Backend startup validation that rejects an outdated or unversioned database schema
- Confirmed document deletion with database cascades and guarded cleanup of the uploaded PDF, page images, and FAISS index
- Dashboard document history with status, extraction counts, workspace links, and per-document deletion controls

Docker and final testing polish are intentionally reserved for later phases.

## Repository layout

```text
.
├── frontend/              React + Vite client
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       └── utils/
└── backend/               FastAPI application
    └── app/
        ├── api/
        ├── core/
        ├── models/
        ├── schemas/
        ├── services/
        └── utils/
```

## Prerequisites

- Node.js 20 or newer
- Python 3.11 or newer
- PostgreSQL 15 or newer

## Create the database

Create an empty PostgreSQL database named `doculens` using pgAdmin or the PostgreSQL CLI:

```powershell
createdb -U postgres doculens
```

Copy `backend/.env.example` to `backend/.env`, then replace `change-me` in `DOCULENS_DATABASE_URL` with your PostgreSQL password. If your username, host, port, or database name differs, update those values as well.

For a new empty database, create the complete schema with:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

This workspace's existing database has already been adopted and upgraded to the Phase 11 head. For another pre-Phase-11 database whose tables were created by this application, adopt the existing Phase 10 schema once, then upgrade it:

```powershell
.\.venv\Scripts\alembic.exe stamp 20260910_01
.\.venv\Scripts\alembic.exe upgrade head
```

Do not stamp an unknown or manually modified database; inspect or migrate it explicitly first. Backend startup now verifies that the database is at the current Alembic head.

## Run the backend

From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install paddlepaddle==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.download_ocr_models
python -m scripts.download_embedding_model
alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, leave the environment unactivated and use `.\.venv\Scripts\python.exe` in place of `python` for the install and Uvicorn commands.

API documentation is available at <http://127.0.0.1:8000/docs>. The health endpoint is <http://127.0.0.1:8000/health>.

### Run Backend

```bash
cd backend
python run.py
```

## Run the frontend

In a second PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Open <http://127.0.0.1:5173>. The dashboard should show **Backend connected** when both applications are running.

Open the Upload page, select a genuine PDF no larger than 50 MB, and choose **Upload document**. A successful upload navigates to the primary document workspace. Choose **Process document** and verify the `CONVERTING`, `PREPROCESSING`, `OCR_PROCESSING`, `EXTRACTING_ENTITIES`, `INDEXING`, and **Processing complete** stages. Use the left page rail or previous/next controls to navigate, then enable **Regions** on the enhanced image. Hover or keyboard-focus a region to see its OCR text and confidence. In the Entities tab, select an entity to navigate to and highlight its source area. In the Search tab, enter a natural-language query and choose a ranked result to jump to its referenced page. Overlays are intentionally disabled on the original image because preprocessing resize and deskew operations can change its coordinate system.

After processing completes, choose JSON, CSV, or TXT in the workspace header and select **Export**. The browser should download the requested format using a safe derivative of the original PDF filename.

Documents processed before Phase 9 show a **Build search index** action. Use it once to create their chunks and local FAISS index without rerunning OCR or entity extraction.

## Run checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app

cd ..\frontend
npm.cmd run lint
npm.cmd run build
```

## Configuration

Backend settings use the `DOCULENS_` prefix. Frontend variables use Vite's `VITE_` prefix. The checked-in `.env.example` files document all current values.

## Current API

- `GET /documents` - lists all retained uploads newest first
- `GET /documents/{document_id}` - returns metadata and conversion status
- `DELETE /documents/{document_id}` - permanently deletes an idle document and its local artifacts
- `POST /documents/{document_id}/process` - starts background conversion and preprocessing
- `GET /documents/{document_id}/pages` - returns ordered page metadata
- `GET /documents/{document_id}/pages/{page_number}` - returns page text, confidence, and OCR regions
- `GET /documents/{document_id}/entities` - returns all stored entities; accepts an optional `page_number` query parameter
- `POST /documents/{document_id}/search` - returns ranked semantic matches with scores and page references
- `GET /documents/{document_id}/export?format=json|csv|txt` - downloads metadata and extracted information
- `GET /documents/{document_id}/pages/{page_number}/image` - serves an original or `?variant=preprocessed` page PNG
- `GET /health` — reports API health
- `POST /documents/upload` — accepts one multipart PDF in the `file` field

## Offline operation

No document content is sent to a cloud inference service. Run `python -m scripts.download_ocr_models` and `python -m scripts.download_embedding_model` once while online. PaddleOCR and `all-MiniLM-L6-v2` are then stored in the gitignored `backend/models_cache` directory, while per-document FAISS files are stored in `backend/search_indexes`. The `en_core_web_sm` spaCy pipeline is installed with the Python dependencies. OCR, entity extraction, indexing, search, and export generation all work locally without an internet connection after setup.

## Planned architecture

```text
React frontend → FastAPI REST API → processing services
                                      ├── PostgreSQL metadata
                                      ├── local files
                                      └── local FAISS index
```

## Screenshots

Screenshots will be added as the document workspace is implemented.
