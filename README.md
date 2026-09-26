# DocuQuery

DocuQuery is a Cloud-Native AI Document Processor — a Retrieval-Augmented
Generation (RAG) application that lets you upload PDF documents and ask
natural-language questions about their contents, with answers grounded in
the actual document text.

## Architecture

Monorepo structure:
- `backend/` — Python FastAPI service handling PDF ingestion, chunking,
  embeddings, vector storage, and retrieval-augmented question answering
- `frontend/` — React (Vite) application with a document upload UI and
  chat-style query interface
- `infra/` — Docker and Grafana configuration for containerization and
  observability

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **LLM & Embeddings**: Ollama (local) — `llama3.2` for generation,
  `nomic-embed-text` for embeddings
- **Database**: PostgreSQL with the `pgvector` extension for vector
  similarity search
- **Frontend**: React (Vite), Tailwind CSS v4
- **DevOps**: Docker, Docker Compose (planned), GitHub Actions CI/CD (planned)
- **Observability**: Prometheus, Grafana (planned)

## Current Status

- **Phase 1 — Project Setup**: ✅ Done
- **Phase 2 — Backend & RAG Pipeline**: ✅ Done — PDF ingestion, chunking,
  local embeddings, pgvector storage, and grounded question-answering all
  working via `/upload` and `/query`
- **Phase 3 — Frontend**: ⏳ In progress
- **Phase 4–6 — Containerization, Observability, CI/CD**: Planned

## Getting Started (local development)

1. **Backend setup**
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

2. **Local models** — install [Ollama](https://ollama.com), then:

ollama pull llama3.2
ollama pull nomic-embed-text

3. **Database** — Postgres with pgvector, via Docker:

docker run --name docuquery-pg
-e POSTGRES_USER=docuquery -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=docuquery
-p 5432:5432 -d pgvector/pgvector:pg16

4. **Run the API**

uvicorn backend.main:app --reload --port 8000

   Visit `http://localhost:8000/docs` for the interactive API explorer.

## API Endpoints

| Endpoint  | Method | Description                          |
|-----------|--------|---------------------------------------|
| `/health` | GET    | Health check                          |
| `/upload` | POST   | Upload a PDF, returns chunk count     |
| `/query`  | POST   | Ask a question, returns a grounded answer |