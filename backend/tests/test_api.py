from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.main import app
import backend.routes as routes


client = TestClient(app)


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are allowed."}


def test_upload_returns_document_id_and_chunk_count(monkeypatch):
    def fake_ingest(file_path, document_id, filename):
        assert file_path.endswith(".pdf")
        UUID(document_id)
        assert filename == "resume.pdf"
        return 3

    monkeypatch.setattr(routes, "ingest_pdf", fake_ingest)

    response = client.post(
        "/upload",
        files={"file": ("resume.pdf", b"fake pdf", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    UUID(payload["document_id"])
    assert payload["filename"] == "resume.pdf"
    assert payload["chunks_created"] == 3


def test_query_requires_document_id():
    response = client.post("/query", json={"question": "What is this about?"})

    assert response.status_code == 422


def test_query_returns_answer_and_sources(monkeypatch):
    document_id = uuid4()

    def fake_query(question, requested_document_id):
        assert question == "What experience is listed?"
        assert requested_document_id == str(document_id)
        return (
            "The document lists cloud engineering experience.",
            [{"filename": "resume.pdf", "page": 2}],
        )

    monkeypatch.setattr(routes, "query_documents", fake_query)

    response = client.post(
        "/query",
        json={
            "question": "What experience is listed?",
            "document_id": str(document_id),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The document lists cloud engineering experience.",
        "sources": [{"filename": "resume.pdf", "page": 2}],
    }
