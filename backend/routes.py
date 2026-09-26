from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
import tempfile
import os

from .rag_pipeline import ingest_pdf, query_documents


router = APIRouter()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


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

        chunk_count = ingest_pdf(temp_path)

        return {
            "filename": file.filename,
            "chunks_created": chunk_count,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/query", response_model=QueryResponse)
def query_pdf(request: QueryRequest):
    answer = query_documents(request.question)
    return QueryResponse(answer=answer)