from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
import tempfile
import os
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .rag_pipeline import ingest_pdf, query_documents
from .metrics import QUERIES, QUERY_LATENCY
from .auth import authenticate_user, create_access_token, create_user, get_current_user
from .database import DocumentRecord, User, get_db
from .jobs import process_document


router = APIRouter()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
UPLOAD_READ_SIZE = 1024 * 1024


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_id: UUID


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class UploadResponse(BaseModel):
    document_id: UUID
    filename: str
    status: str
    chunks_created: int = 0


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    filename: str
    status: str
    chunks_created: int
    error: Optional[str] = None


class Source(BaseModel):
    filename: str
    page: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


def save_document(db: Session, document_id: str, owner_id: str, filename: str) -> None:
    db.add(
        DocumentRecord(
            id=document_id,
            owner_id=owner_id,
            filename=filename,
            chunks_created=0,
            status="processing",
        )
    )
    db.commit()


def find_owned_document(db: Session, document_id: str, owner_id: str) -> Optional[DocumentRecord]:
    return (
        db.query(DocumentRecord)
        .filter(
            DocumentRecord.id == document_id,
            DocumentRecord.owner_id == owner_id,
        )
        .first()
    )


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(credentials: Credentials, db: Session = Depends(get_db)):
    try:
        user = create_user(db, credentials.username, credentials.password)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists.") from exc

    return AuthResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
        username=user.username,
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return AuthResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
        username=user.username,
    )


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
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
        save_document(db, document_id, current_user.id, file.filename)
        background_tasks.add_task(
            process_document,
            temp_path,
            document_id,
            current_user.id,
            file.filename,
        )
        temp_path = None

        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processing",
            "chunks_created": 0,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/documents/{document_id}", response_model=DocumentStatusResponse)
def document_status(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = find_owned_document(db, str(document_id), current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentStatusResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        chunks_created=document.chunks_created,
        error=document.error,
    )


@router.post("/query", response_model=QueryResponse)
def query_pdf(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document_id = str(request.document_id)
    document = find_owned_document(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    if document.status == "processing":
        raise HTTPException(status_code=409, detail="Document is still processing.")
    if document.status == "failed":
        raise HTTPException(status_code=422, detail=document.error or "Document processing failed.")

    try:
        with QUERY_LATENCY.time():
            answer, sources = query_documents(
                request.question,
                document_id,
                current_user.id,
            )
    except Exception:
        QUERIES.labels(status="error").inc()
        raise

    QUERIES.labels(status="success").inc()
    return QueryResponse(answer=answer, sources=sources)
