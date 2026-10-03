import os

from .database import DocumentRecord, SessionLocal
from .metrics import CHUNKS_CREATED, DOCUMENT_UPLOADS
from .rag_pipeline import ingest_pdf


def process_document(
    temp_path: str,
    document_id: str,
    owner_id: str,
    filename: str,
) -> None:
    db = SessionLocal()
    document = db.get(DocumentRecord, document_id)

    try:
        chunk_count = ingest_pdf(temp_path, document_id, filename, owner_id)
        document.chunks_created = chunk_count
        document.status = "completed"
        document.error = None
        CHUNKS_CREATED.inc(chunk_count)
        DOCUMENT_UPLOADS.labels(status="success").inc()
        db.commit()
    except Exception as exc:
        if document:
            document.status = "failed"
            document.error = str(exc)[:1000]
            db.commit()
        DOCUMENT_UPLOADS.labels(status="error").inc()
    finally:
        db.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)
