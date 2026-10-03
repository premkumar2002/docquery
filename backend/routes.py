from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
import tempfile
import os
from uuid import UUID, uuid4
from typing import Optional

from .rag_pipeline import ingest_pdf, query_documents


router = APIRouter()


class QueryRequest(BaseModel):
    question: str
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
            contents = await file.read()
            temp_file.write(contents)

        document_id = str(uuid4())
        chunk_count = ingest_pdf(temp_path, document_id, file.filename)

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
    answer, sources = query_documents(
        request.question,
        str(request.document_id),
    )
    return QueryResponse(answer=answer, sources=sources)
