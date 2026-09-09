# Codex Master Prompt for ARCIL Document Intelligence Project

You are implementing a production-style offline document intelligence platform for an ARCIL hiring assignment.

## Project Goal

Build a full-stack application that accepts a scanned PDF document of around 50 pages and extracts relevant information from it using an offline AI/ML pipeline.

The system should be designed like a real enterprise document-processing platform, not just a basic OCR demo.

The final system should support:

- Uploading scanned PDF documents
- Converting each PDF page into an image
- Image preprocessing using OpenCV
- OCR using an offline OCR model
- Storing page-level extracted text
- Extracting structured information such as names, dates, organizations, monetary values, IDs, percentages, etc.
- Semantic search across the document
- Page-level source traceability
- OCR confidence
- Bounding-box coordinates for extracted text
- Highlighting extracted information directly on the scanned page
- JSON / CSV export
- Completely offline document processing after required model files are installed

Do not use cloud APIs such as Gemini, OpenAI, AWS Textract, Azure OCR, Google Vision API, or any online inference service.

---

## Required Tech Stack

### Frontend

Use:

- React.js
- Vite
- JavaScript
- Tailwind CSS
- React Router
- Axios

Do not use Next.js.

### Backend

Use:

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### Database

Use:

- PostgreSQL

Use SQLAlchemy ORM.

### PDF Processing

Use:

- PyMuPDF / fitz

### Image Processing

Use:

- OpenCV

### OCR

Primary OCR engine:

- PaddleOCR

The OCR model must run locally/offline.

Preserve:

- extracted text
- confidence score
- bounding box coordinates

### NLP / Structured Information Extraction

Use:

- spaCy
- Python regular expressions

spaCy should handle general named entities.

Regex should handle structured patterns such as:

- dates
- currency values
- percentages
- email addresses
- phone numbers
- PAN-like identifiers where relevant
- account/reference numbers
- other financial-document patterns

### Semantic Search

Use:

- sentence-transformers
- all-MiniLM-L6-v2
- FAISS

The embedding model and vector search must work offline after installation.

### Local Storage

Initially store:

- uploaded PDFs
- generated page images
- preprocessed images

on the local filesystem.

Metadata and extracted text should be stored in PostgreSQL.

### Containerization

Add Docker support only after the core system works correctly.

---

## System Architecture

Follow this architecture strictly:

```text
React Frontend
    |
    | REST API
    v
FastAPI Backend
    |
    +-- Document Upload Service
    +-- PDF Processing Service
    +-- Image Preprocessing Service
    +-- OCR Service
    +-- Entity Extraction Service
    +-- Semantic Search Service
    +-- Export Service
    |
    +-- PostgreSQL
    |
    +-- Local File Storage
    |
    +-- FAISS Index
```

The frontend must never directly invoke OCR, OpenCV, spaCy, FAISS, or other ML components.

FastAPI should orchestrate the complete backend pipeline.

Maintain clean separation of concerns.

---

## Required Project Structure

Create the repository as a monorepo using approximately this structure:

```text
doculens-ai/
|
+-- frontend/
|   |
|   +-- src/
|       +-- components/
|       +-- pages/
|       +-- services/
|       +-- hooks/
|       +-- utils/
|       +-- App.jsx
|       +-- main.jsx
|
|   +-- public/
|   +-- package.json
|   +-- vite.config.js
|
+-- backend/
|   |
|   +-- app/
|       |
|       +-- api/
|       |   +-- documents.py
|       |   +-- search.py
|       |   +-- extraction.py
|       |
|       +-- core/
|       |   +-- config.py
|       |   +-- database.py
|       |
|       +-- models/
|       |   +-- document.py
|       |   +-- page.py
|       |   +-- entity.py
|       |   +-- document_chunk.py
|       |
|       +-- schemas/
|       |   +-- document.py
|       |   +-- page.py
|       |   +-- entity.py
|       |   +-- search.py
|       |
|       +-- services/
|       |   +-- document_service.py
|       |   +-- pdf_service.py
|       |   +-- preprocessing_service.py
|       |   +-- ocr_service.py
|       |   +-- entity_service.py
|       |   +-- embedding_service.py
|       |   +-- search_service.py
|       |   +-- export_service.py
|       |
|       +-- utils/
|       |
|       +-- main.py
|
|   +-- uploads/
|   +-- processed/
|   +-- requirements.txt
|   +-- .env.example
|
+-- docker-compose.yml
+-- .gitignore
+-- README.md
```

You may introduce additional folders where justified, but do not collapse the backend into one or two giant files.

---

## Core Database Models

Implement at least these entities.

### Document

Fields should include:

- id
- original_filename
- stored_filename
- file_path
- page_count
- status
- created_at
- processed_at
- error_message if processing fails

### Page

Fields should include:

- id
- document_id
- page_number
- original_image_path
- preprocessed_image_path
- raw_text
- cleaned_text
- average_ocr_confidence
- created_at

### Entity

Fields should include:

- id
- document_id
- page_id
- entity_type
- entity_value
- confidence if available
- source
- bounding_box if available

### DocumentChunk

Fields should include:

- id
- document_id
- page_number
- content
- chunk_index
- vector reference or FAISS mapping information

Use proper SQLAlchemy relationships.

---

## Document Processing Status

Do not use only a boolean processing flag.

Use explicit states:

- UPLOADED
- CONVERTING
- PREPROCESSING
- OCR_PROCESSING
- EXTRACTING_ENTITIES
- INDEXING
- COMPLETED
- FAILED

Keep the current processing status in the database.

The frontend should be able to display these states.

---

## Required API Design

Implement clean REST APIs.

At minimum:

### `POST /documents/upload`

Purpose: Upload a scanned PDF.

Return:

- document_id
- filename
- status

### `GET /documents`

Purpose: List uploaded documents.

### `GET /documents/{document_id}`

Purpose: Return document metadata and processing status.

### `POST /documents/{document_id}/process`

Purpose: Run the processing pipeline.

### `GET /documents/{document_id}/pages`

Purpose: Return page metadata.

### `GET /documents/{document_id}/pages/{page_number}`

Purpose: Return page OCR content, OCR confidence, image paths, bounding boxes, and extracted information.

### `GET /documents/{document_id}/entities`

Purpose: Return extracted structured entities.

### `POST /documents/{document_id}/search`

Request:

```json
{
  "query": "What is the loan amount?"
}
```

Response should contain ranked search results with:

- page_number
- text
- score
- relevant source information

### `GET /documents/{document_id}/export`

Support:

- JSON
- CSV where practical

Use proper Pydantic request and response schemas.

---

## Frontend Pages

### Dashboard

Route:

`/`

Display:

- application name
- uploaded documents
- processing status
- page count
- creation date
- actions to open document

### Upload Page

Route:

`/upload`

Features:

- drag-and-drop or file picker
- PDF validation
- upload progress
- useful error handling
- navigate to document workspace after upload

### Document Workspace

Route:

`/documents/:id`

This should be the primary interface.

Recommended layout:

Left sidebar:

- document pages
- page numbers
- page thumbnails if practical

Main content:

- selected scanned page
- extracted text
- page metadata
- OCR confidence

Right-side information panel or tabbed area:

- extracted entities
- document summary
- search
- processing status

### Page Inspector

Route:

`/documents/:id/pages/:pageNumber`

Features:

- full scanned page image
- OCR text
- OCR confidence
- extracted entities
- bounding-box highlighting

---

## Important UX Requirement

Implement page-level traceability.

For every OCR text region, preserve bounding boxes from PaddleOCR.

Example:

```json
{
  "text": "₹25,00,000",
  "confidence": 0.96,
  "bounding_box": [
    [381, 490],
    [492, 490],
    [492, 523],
    [381, 523]
  ]
}
```

The frontend should eventually be able to overlay bounding boxes over the scanned page image.

This is a major feature.

Do not discard OCR coordinates.

---

## Processing Pipeline

The backend processing pipeline should follow this exact logical order:

1. Validate uploaded PDF
2. Save PDF locally
3. Create database document record
4. Convert PDF pages to images using PyMuPDF
5. Store page records
6. Preprocess images using OpenCV
7. Perform OCR using PaddleOCR
8. Store OCR text, confidence, and bounding boxes
9. Clean OCR text
10. Extract entities using spaCy and regex
11. Store entities
12. Chunk document text
13. Generate embeddings using sentence-transformers
14. Build / update FAISS index
15. Mark document COMPLETED

If any stage fails:

- log the error
- set document status to FAILED
- store an appropriate error message
- do not silently swallow exceptions

---

## OpenCV Preprocessing

Create a reusable preprocessing pipeline.

Include practical operations where appropriate:

- grayscale
- denoising
- thresholding
- contrast enhancement
- resizing
- deskewing

Do not blindly apply aggressive processing that may reduce OCR accuracy.

Design preprocessing so steps can later be adjusted independently.

---

## OCR Service

Create a dedicated OCR service.

It should:

- initialize PaddleOCR efficiently
- avoid loading the OCR model separately for every page
- process each page
- return structured OCR output

Recommended internal result shape:

```json
{
  "page_number": 1,
  "blocks": [
    {
      "text": "...",
      "confidence": 0.98,
      "bounding_box": []
    }
  ],
  "full_text": "...",
  "average_confidence": 0.94
}
```

Do not reduce OCR output to just a string.

---

## Entity Extraction

Build two complementary extraction systems.

### spaCy

Use offline NER for general entities such as:

- PERSON
- ORG
- DATE
- GPE
- MONEY

### Regex

Create modular extraction patterns for:

- currency
- dates
- percentages
- emails
- phone numbers
- identifiers
- financial values

Make regex extractors reusable and testable.

Avoid placing every regex inside one huge function.

---

## Semantic Search

Implement semantic search only after OCR and entity extraction are stable.

Pipeline:

```text
cleaned page text
    ->
text chunking
    ->
sentence-transformers embeddings
    ->
FAISS index
```

Use:

`sentence-transformers/all-MiniLM-L6-v2`

Search results should return:

- content
- similarity score
- page number
- chunk index

Keep enough metadata so the user can jump directly to the source page.

---

## Offline Requirement

This is a critical assignment constraint.

The final processing pipeline must not depend on external APIs.

After local models are downloaded and installed, the application should continue functioning without internet access.

Document contents must never be sent outside the machine.

Add a README section explaining this clearly.

---

## Security and File Validation

Implement basic practical protections.

At minimum:

- accept PDF files only
- reject invalid MIME/file formats
- avoid using user-provided filenames directly as filesystem paths
- generate UUID-based stored filenames
- configure maximum upload size where practical
- use safe path handling
- validate document existence before processing APIs

---

## Code Quality Requirements

Follow these rules strictly:

1. Keep route handlers thin.
2. Put processing logic in service classes/functions.
3. Do not create giant files.
4. Do not duplicate logic.
5. Use clear names.
6. Use type hints in Python.
7. Use Pydantic schemas.
8. Add comments only when they explain non-obvious reasoning.
9. Avoid unnecessary abstractions.
10. Prefer readable code over overly clever code.
11. Maintain clear error handling.
12. Use environment variables for configuration.
13. Add `.env.example`.
14. Do not commit model binaries, uploaded PDFs, generated page images, local databases, virtual environments, or `node_modules`.
15. Add an appropriate `.gitignore`.

---

# Development Phases

You MUST implement the project phase-by-phase.

Do not jump ahead.

## Phase 1 — Project Foundation

Implement:

- monorepo folders
- React + Vite app
- Tailwind CSS
- FastAPI app
- CORS
- health endpoint
- frontend Axios API client
- environment configuration
- README starter documentation

Success criteria:

Frontend runs successfully.

Backend runs successfully.

Frontend can call:

`GET /health`

and display or verify a successful response.

---

## Phase 2 — Document Upload

Implement:

- Upload page
- PDF file picker / drag-drop
- client-side basic validation
- `POST /documents/upload`
- UUID-based filenames
- local PDF storage
- document database record
- returned document ID
- upload error handling

Success criteria:

A scanned PDF can be uploaded through React and is stored correctly by FastAPI.

---

## Phase 3 — PDF Page Conversion

Implement:

- PyMuPDF page conversion
- one image per PDF page
- correct page ordering
- page database records
- GET document pages API
- frontend page list

Success criteria:

A 50-page PDF results in 50 page records/images and the frontend can display them.

---

## Phase 4 — Image Preprocessing

Implement:

- OpenCV preprocessing service
- grayscale
- denoise
- thresholding
- optional deskew
- save preprocessed images
- preserve original images

Success criteria:

Original and preprocessed versions are both available for every page.

---

## Phase 5 — OCR

Implement PaddleOCR.

Requirements:

- process each page
- preserve bounding boxes
- preserve confidence values
- store raw OCR text
- calculate average page confidence
- update progress/status

Frontend should display:

- OCR text
- confidence
- selected page

Success criteria:

A scanned PDF can be processed fully and OCR text can be inspected page-by-page.

---

## Phase 6 — Entity Extraction

Implement:

- spaCy NER
- regex extractors
- entity storage
- `/entities` API
- frontend entity panel

Success criteria:

Relevant entities are visible alongside the page/document.

---

## Phase 7 — Document Workspace

Build polished document workspace.

Include:

- page navigation
- page preview
- OCR text
- OCR confidence
- processing status
- extracted entities
- document metadata

Do not sacrifice functionality for visual complexity.

---

## Phase 8 — Bounding Box Visualization

Overlay OCR bounding boxes over document images.

Requirements:

- coordinate transformation must account for displayed image scale
- clicking an extracted entity should highlight its source region where possible
- hovering an OCR region may display text/confidence

Success criteria:

The user can visually verify where extracted text came from.

---

## Phase 9 — Semantic Search

Implement:

- chunking
- local embeddings
- FAISS
- search API
- search UI
- ranked results
- page references

Clicking a search result should navigate to the relevant document page.

---

## Phase 10 — Export

Implement export to:

- JSON
- CSV where appropriate
- optionally plain extracted text

Exports should contain document metadata and extracted information.

---

## Phase 11 — PostgreSQL / Persistence Hardening

If PostgreSQL was not introduced earlier, fully migrate to it now.

Ensure:

- relationships are correct
- indexes exist for common lookups
- document deletion does not leave broken page/entity references
- migration setup is documented

Prefer Alembic for migrations.

---

## Phase 12 — Dockerization

Create:

- Dockerfile for frontend
- Dockerfile for backend
- `docker-compose.yml`
- PostgreSQL service

Do not Dockerize before the application works locally.

---

## Phase 13 — Testing and Final Polish

Add tests for important backend functionality.

At minimum test:

- upload validation
- document lookup
- page generation
- regex extraction
- search metadata
- invalid document IDs

Add meaningful loading and error states to the frontend.

Improve README with:

- setup instructions
- architecture
- system requirements
- model installation steps
- offline operation explanation
- screenshots section placeholder
- API overview

---

## Development Workflow Rules for Codex

Follow this workflow throughout the implementation.

Before modifying files for a phase:

1. Inspect the current repository.
2. Understand existing implementation.
3. Explain briefly what needs to change.
4. Implement only that phase.
5. Run appropriate tests/build/lint checks.
6. Fix errors.
7. Summarize what was implemented.
8. List exact commands I should run locally.
9. Tell me what I should manually verify.
10. Stop before starting the next phase.

Do NOT automatically implement every future phase unless I explicitly ask you to continue.

I want incremental, reviewable development.

Do not rewrite working architecture unnecessarily.

Do not delete existing functioning code unless required.

---

## Git Workflow

Keep the implementation commit-friendly.

Each phase should be logically isolated so I can commit it separately.

Suggested commit style:

```text
feat: initialize frontend and FastAPI backend

feat: add document upload pipeline

feat: convert PDF pages to images

feat: add image preprocessing pipeline

feat: integrate offline PaddleOCR

feat: add entity extraction

feat: build document workspace

feat: visualize OCR bounding boxes

feat: add semantic document search

feat: add document exports

chore: dockerize application
```

Do not automatically run `git push`.

Do not rewrite Git history.

---

# Current Instruction

Start ONLY with Phase 1.

First inspect the repository.

If the repository is empty, initialize the required project structure.

Implement:

- React + Vite frontend
- JavaScript
- Tailwind CSS
- FastAPI backend
- CORS
- `/health` endpoint
- Axios client
- frontend-to-backend connectivity
- basic folder structure
- `.gitignore`
- `.env.example`
- README

Do not implement PDF upload, OCR, database models, PostgreSQL, spaCy, PaddleOCR, OpenCV, FAISS, Docker, or semantic search yet.

After implementing Phase 1:

- run available checks
- report files created or modified
- provide exact commands to run frontend and backend
- tell me what I should see when everything is working
- stop and wait for my instruction to continue to Phase 2
