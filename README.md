# DocuQuery

DocuQuery is a cloud-native AI document processor built around Retrieval-Augmented Generation (RAG). Users upload PDF documents and ask natural-language questions about their contents. The application extracts and chunks the document, creates embeddings, stores them in PostgreSQL with pgvector, retrieves relevant context, and generates an answer with a local LLM.

The project is intentionally being built in production-oriented phases to demonstrate backend engineering, AI application development, frontend integration, observability, containerization, and CI/CD.

## Current Features

- PDF upload from a React web interface
- PDF text extraction and recursive text chunking
- Local embeddings with Ollama's `nomic-embed-text`
- Vector similarity search with PostgreSQL and pgvector
- Grounded question answering with Ollama's `llama3.2`
- Document-scoped retrieval to prevent cross-document answers
- Source references with filenames and page numbers
- FastAPI `/upload`, `/query`, and `/health` endpoints
- Chat-style question and answer history in the frontend
- Client-side PDF validation, loading states, and user-facing errors
- Server-side PDF signature, size, and question-length validation
- Prompt-injection-aware RAG instructions that treat document text as untrusted
- JWT authentication with Argon2 password hashing and PostgreSQL-backed ownership
- Background PDF ingestion with processing status and failure reporting
- Responsive Tailwind CSS interface
- Dockerfiles for the backend and production frontend image
- Docker Compose stack for PostgreSQL, FastAPI, and the frontend
- Prometheus metrics, request IDs, structured request logs, and a provisioned Grafana dashboard
- GitHub Actions CI for backend tests, frontend checks, container builds, and dependency audits

## Architecture

```text
React + Vite frontend
        |
        | multipart PDF upload / JSON question
        v
FastAPI backend
        |
        +--> PyPDFLoader --> text splitter --> Ollama embeddings
        |                                      |
        |                                      v
        |                               PostgreSQL + pgvector
        |
        +--> similarity search --> retrieved context --> Ollama LLM --> answer
```

Monorepo structure:

```text
docuquery/
├── backend/       # FastAPI API and RAG pipeline
├── frontend/      # React + Vite + Tailwind UI
├── infra/         # Infrastructure and observability configuration
└── README.md
```

## Tech Stack

| Area | Technology |
|---|---|
| API | Python, FastAPI, Pydantic |
| RAG | LangChain, recursive text splitting, vector similarity search |
| LLM and embeddings | Ollama, `llama3.2`, `nomic-embed-text` |
| Database | PostgreSQL with the pgvector extension |
| Frontend | React, Vite, Tailwind CSS v4 |
| Local infrastructure | Docker |
| Planned delivery | GitHub Actions, Docker Compose, Grafana, Prometheus |

## Project Status

- **Phase 1 — Project setup:** ✅ Complete
- **Phase 2 — Backend and RAG pipeline:** ✅ Complete — document-scoped retrieval and source citations included
- **Phase 3 — Frontend MVP:** ✅ Complete
- **Phase 4 — Containerization and local DevOps:** ✅ Initial Compose stack complete
- **Phase 5 — Observability and monitoring:** ✅ Initial metrics and dashboard complete
- **Phase 6 — CI/CD and deployment:** ✅ Initial GitHub Actions pipeline complete; cloud deployment planned

## Local Development

### Prerequisites

- Python 3.9+
- Node.js and npm
- Docker Desktop
- [Ollama](https://ollama.com)

### 1. Clone and configure the repository

```bash
git clone https://github.com/premkumar2002/docquery.git
cd docquery
```

Create `backend/.env` with values appropriate for your local environment:

```dotenv
DATABASE_URL=postgresql+psycopg://docuquery:devpassword@localhost:5432/docuquery
OLLAMA_BASE_URL=http://localhost:11434
JWT_SECRET=replace-this-with-a-long-random-secret
```

Do not commit `.env` files or real credentials.

### 2. Start PostgreSQL with pgvector

```bash
docker run --name docuquery-pg \
  -e POSTGRES_USER=docuquery \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=docuquery \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

If the container already exists but is stopped:

```bash
docker start docuquery-pg
```

### 3. Install and start Ollama models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Make sure the Ollama service is running before querying documents.

### 4. Install backend dependencies and run the API

From the repository root:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The API and interactive OpenAPI documentation are available at:

- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### 5. Install and run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, upload a PDF, and ask a question about it.

The first visit prompts you to create an account or sign in. PDF ingestion runs in the background; the UI waits for the document to reach `completed` before enabling questions.

### Docker Compose

The Compose stack runs PostgreSQL/pgvector, the FastAPI backend, and the production frontend. The backend container connects to Ollama running on the host machine through `host.docker.internal`.

```bash
docker compose up --build
```

Open `http://localhost:5173`. Stop the stack with `Ctrl+C`, or run:

```bash
docker compose down
```

Install Ollama and pull both models on the host before using the containerized backend.

When running Compose, the observability tools are also available at:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (default local credentials: `admin` / `admin`)
- Backend metrics: `http://localhost:8000/metrics`

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Returns API health status |
| `/upload` | `POST` | Accepts a PDF and returns a document ID and chunk count |
| `/query` | `POST` | Retrieves document-scoped chunks and returns an answer with sources |
| `/documents/{document_id}` | `GET` | Returns document processing status for the authenticated owner |
| `/auth/register` | `POST` | Creates a user and returns a JWT |
| `/auth/login` | `POST` | Authenticates a user and returns a JWT |

Example query request:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What experience does this person have?"}'
```

## Verification

Frontend checks currently include:

```bash
cd frontend
npm run lint
npm run build
```

Backend tests currently include API contract tests, upload validation tests, metadata tests, document filter tests, and empty-result behavior:

```bash
source backend/venv/bin/activate
pytest -q
```

The backend can be smoke-tested with:

```bash
curl http://localhost:8000/health
```

Prometheus metrics can be checked with:

```bash
curl http://localhost:8000/metrics
```

## Production-Focused Roadmap

The following milestones are ordered to turn the MVP into a stronger portfolio project and demonstrate skills commonly requested for backend, platform, and AI engineering roles.

### 1. Document isolation and metadata

✅ **Complete in the current MVP.** Each upload receives a document ID, chunks carry filename/page metadata, and query responses include source references.

- Give every upload a document ID and persist document metadata.
- Scope retrieval to a selected document or workspace instead of one shared collection.
- Return source filenames and page numbers with every answer.

**Skills demonstrated:** data modeling, multi-tenant boundaries, API design, trustworthy RAG.

### 2. Automated testing and evaluation

✅ **Initial API and RAG contract tests are complete.** The remaining work is integration testing against a real pgvector service and adding a golden evaluation dataset.

- Add `pytest` unit tests for chunking, validation, and API behavior.
- Add integration tests with a temporary PostgreSQL/pgvector service.
- Create a small golden question-and-answer dataset.
- Measure retrieval quality, answer faithfulness, latency, and failure cases.

**Skills demonstrated:** test strategy, integration testing, AI evaluation, regression prevention.

### 3. Async ingestion and production reliability

✅ **Initial background processing is complete.** Uploads create a processing record, run ingestion after the response, expose status through `/documents/{document_id}`, and report failures to the UI.

- Move PDF processing to a background job queue.
- Add upload status endpoints: queued, processing, complete, failed.
- Add file size limits, timeouts, retries, and structured error responses.

**Skills demonstrated:** asynchronous systems, resilience, API contracts, operational thinking.

### 4. Authentication and security

✅ **Authentication and initial input-safety controls are complete.** Users receive JWTs, documents are owned by the authenticated user, uploads are streamed with a size limit, PDF signatures are checked, question length is bounded, and document content is treated as untrusted by the prompt.

- Add refresh tokens, account recovery, and production secret-manager integration.
- Store secrets through environment or secret-manager configuration.
- Add rate limiting, input validation, audit logging, and prompt-injection defenses.

**Skills demonstrated:** secure application design, authorization, threat modeling.

### 5. Observability

✅ **Initial observability is complete.** The API exposes Prometheus metrics, request IDs, structured request logs, and a provisioned Grafana dashboard.

- Add Prometheus metrics for upload count, chunk count, query latency, and failures.
- Add structured JSON logs with request IDs.
- Add Grafana dashboards and distributed tracing with OpenTelemetry.

**Skills demonstrated:** SRE fundamentals, monitoring, debugging production systems.

### 6. Containerization and deployment

- Add Dockerfiles for backend and frontend.
- Add Docker Compose for the full local stack.
- Deploy the API, frontend, and managed PostgreSQL to a cloud platform.
- Add health checks, resource limits, and environment-specific configuration.

**Skills demonstrated:** Docker, cloud deployment, networking, release engineering.

### 7. CI/CD and software supply chain

✅ **Initial CI is complete.** GitHub Actions now runs backend tests, frontend lint/build checks, Compose validation, container builds, and dependency audits on pushes and pull requests.

- Add GitHub Actions for linting, tests, frontend builds, and backend checks.
- Build and scan container images, then publish them to GHCR.
- Add dependency auditing and secret scanning.
- Deploy automatically from a protected main branch.

**Skills demonstrated:** CI/CD, DevSecOps, automation, Git workflows.

## Resume Positioning

Once the next milestones are complete, a strong project bullet could look like:

> Built and deployed a production-oriented RAG document platform using FastAPI, React, LangChain, PostgreSQL/pgvector, and Ollama; implemented PDF ingestion, semantic retrieval, grounded answers, automated testing, Prometheus/Grafana observability, Docker deployment, and GitHub Actions CI/CD.

Keep the wording aligned with features that are actually implemented and verifiable in the repository.
