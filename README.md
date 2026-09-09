# DocuLens AI

DocuLens AI is an offline-first document intelligence platform for scanned financial documents. The project is being built incrementally for the ARCIL document extraction assignment.

## Current milestone: Phase 1

This phase establishes the full-stack foundation:

- React, Vite, JavaScript, Tailwind CSS, React Router, and Axios frontend
- FastAPI backend with environment-based settings and CORS
- `GET /health` connectivity check
- A dashboard that reports the live backend status

Document upload, PostgreSQL persistence, PDF conversion, OCR, entity extraction, semantic search, exports, and Docker are intentionally reserved for later phases.

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

## Run the backend

From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation, leave the environment unactivated and use `.\.venv\Scripts\python.exe` in place of `python` for the install and Uvicorn commands.

API documentation is available at <http://127.0.0.1:8000/docs>. The health endpoint is <http://127.0.0.1:8000/health>.

## Run the frontend

In a second PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Open <http://127.0.0.1:5173>. The dashboard should show **Backend connected** when both applications are running.

## Configuration

Backend settings use the `DOCULENS_` prefix. Frontend variables use Vite's `VITE_` prefix. The checked-in `.env.example` files document all current values.

## Offline operation

The finished processing pipeline will use local models only. No document content will be sent to cloud inference services. Internet access is needed only during setup to install dependencies and, in later phases, download model files; after those files are present locally, processing will work without a network connection.

## Planned architecture

```text
React frontend → FastAPI REST API → processing services
                                      ├── PostgreSQL metadata
                                      ├── local files
                                      └── local FAISS index
```

## Screenshots

Screenshots will be added as the document workspace is implemented.

