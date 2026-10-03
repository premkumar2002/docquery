from uuid import UUID, uuid4
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import create_access_token, get_current_user, hash_password, verify_password
from backend.database import get_db
import backend.routes as routes


client = TestClient(app)


class FakeDB:
    pass


app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="test-user")
app.dependency_overrides[get_db] = lambda: FakeDB()


def test_password_hashing_and_tokens():
    hashed_password = hash_password("correct horse battery staple")

    assert hashed_password != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed_password)
    assert not verify_password("wrong password", hashed_password)
    assert create_access_token("user-123")


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are allowed."}


def test_upload_returns_document_id_and_chunk_count(monkeypatch):
    scheduled = {}

    def fake_process(file_path, document_id, owner_id, filename):
        scheduled["job"] = (file_path, document_id, owner_id, filename)

    monkeypatch.setattr(routes, "process_document", fake_process)
    monkeypatch.setattr(routes, "save_document", lambda *args: None)

    response = client.post(
        "/upload",
        files={"file": ("resume.pdf", b"%PDF-1.7 fake pdf", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    UUID(payload["document_id"])
    assert payload["filename"] == "resume.pdf"
    assert payload["status"] == "processing"
    assert payload["chunks_created"] == 0
    assert scheduled["job"][2:] == ("test-user", "resume.pdf")


def test_document_status_returns_processing_state(monkeypatch):
    document_id = uuid4()
    monkeypatch.setattr(
        routes,
        "find_owned_document",
        lambda *args: SimpleNamespace(
            id=str(document_id),
            filename="resume.pdf",
            status="processing",
            chunks_created=0,
            error=None,
        ),
    )

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_upload_rejects_invalid_pdf_signature(monkeypatch):
    response = client.post(
        "/upload",
        files={"file": ("resume.pdf", b"not actually a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "The uploaded file is not a valid PDF."}


def test_query_rejects_questions_over_maximum_length():
    response = client.post(
        "/query",
        json={"question": "x" * 2001, "document_id": str(uuid4())},
    )

    assert response.status_code == 422


def test_query_requires_document_id():
    response = client.post("/query", json={"question": "What is this about?"})

    assert response.status_code == 422


def test_query_returns_answer_and_sources(monkeypatch):
    document_id = uuid4()

    def fake_query(question, requested_document_id, owner_id):
        assert question == "What experience is listed?"
        assert requested_document_id == str(document_id)
        assert owner_id == "test-user"
        return (
            "The document lists cloud engineering experience.",
            [{"filename": "resume.pdf", "page": 2}],
        )

    monkeypatch.setattr(routes, "query_documents", fake_query)
    monkeypatch.setattr(
        routes,
        "find_owned_document",
        lambda *args: SimpleNamespace(id=str(document_id), status="completed"),
    )

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
