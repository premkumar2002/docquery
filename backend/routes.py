from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel, Field
import tempfile
import os
from uuid import UUID, uuid4
from typing import Optional

from .rag_pipeline import ingest_pdf, query_documents
from .metrics import CHUNKS_CREATED, DOCUMENT_UPLOADS, QUERIES, QUERY_LATENCY


router = APIRouter()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
UPLOAD_READ_SIZE = 1024 * 1024


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_id: UUID


class Source(BaseModel):
    filename: str
    page: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


@router.post("/upload")
async def upload_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            total_bytes = 0
            first_chunk = True

            while contents := await file.read(UPLOAD_READ_SIZE):
                total_bytes += len(contents)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"PDF must be smaller than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                    )

                if first_chunk and not contents.startswith(b"%PDF-"):
                    raise HTTPException(
                        status_code=400,
                        detail="The uploaded file is not a valid PDF.",
                    )

                first_chunk = False
                temp_file.write(contents)

            if total_bytes == 0:
                raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

        document_id = str(uuid4())
        try:
            chunk_count = ingest_pdf(temp_path, document_id, file.filename)
        except Exception:
            DOCUMENT_UPLOADS.labels(status="error").inc()
            raise

        DOCUMENT_UPLOADS.labels(status="success").inc()
        CHUNKS_CREATED.inc(chunk_count)

        return {
            "document_id": document_id,
            "filename": file.filename,
            "chunks_created": chunk_count,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/query", response_model=QueryResponse)
def query_pdf(request: QueryRequest):
    try:
        with QUERY_LATENCY.time():
            answer, sources = query_documents(
                request.question,
                str(request.document_id),
            )
    except Exception:
        QUERIES.labels(status="error").inc()
        raise

    QUERIES.labels(status="success").inc()
    return QueryResponse(answer=answer, sources=sources)
