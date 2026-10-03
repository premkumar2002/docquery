from types import SimpleNamespace

from langchain_core.documents import Document

import backend.rag_pipeline as rag_pipeline


def test_ingest_adds_document_and_page_metadata(monkeypatch):
    documents = [
        Document(page_content="first page", metadata={"page": 0}),
        Document(page_content="second page", metadata={"page": 1}),
    ]
    captured = {}

    class FakeVectorStore:
        def add_documents(self, received_documents):
            captured["documents"] = received_documents

    monkeypatch.setattr(rag_pipeline, "chunk_pdf", lambda file_path: documents)
    monkeypatch.setattr(rag_pipeline, "vector_store", FakeVectorStore())

    count = rag_pipeline.ingest_pdf("document.pdf", "doc-123", "resume.pdf", "user-123")

    assert count == 2
    assert captured["documents"][0].metadata == {
        "page": 0,
        "document_id": "doc-123",
        "owner_id": "user-123",
        "filename": "resume.pdf",
        "page_number": 1,
        "source": "resume.pdf",
    }
    assert captured["documents"][1].metadata["page_number"] == 2


def test_query_filters_by_document_and_deduplicates_sources(monkeypatch):
    captured = {}
    documents = [
        Document(
            page_content="cloud engineering",
            metadata={"document_id": "doc-123", "filename": "resume.pdf", "page_number": 2},
        ),
        Document(
            page_content="AWS experience",
            metadata={"document_id": "doc-123", "filename": "resume.pdf", "page_number": 2},
        ),
        Document(
            page_content="automation",
            metadata={"document_id": "doc-123", "filename": "resume.pdf", "page_number": 4},
        ),
    ]

    class FakeVectorStore:
        def similarity_search(self, question, k, filter):
            captured["arguments"] = (question, k, filter)
            return documents

    class FakePrompt:
        def __or__(self, _llm):
            return self

        def invoke(self, values):
            captured["prompt_values"] = values
            return SimpleNamespace(content="Grounded answer")

    monkeypatch.setattr(rag_pipeline, "vector_store", FakeVectorStore())
    monkeypatch.setattr(rag_pipeline, "prompt", FakePrompt())
    monkeypatch.setattr(rag_pipeline, "llm", object())

    answer, sources = rag_pipeline.query_documents(
        "Where did they work?",
        "doc-123",
        "user-123",
    )

    assert answer == "Grounded answer"
    assert captured["arguments"] == (
        "Where did they work?",
        4,
        {"document_id": "doc-123", "owner_id": "user-123"},
    )
    assert "[Source: resume.pdf, page 2]" in captured["prompt_values"]["context"]
    assert sources == [
        {"filename": "resume.pdf", "page": 2},
        {"filename": "resume.pdf", "page": 4},
    ]


def test_query_returns_unknown_when_no_document_chunks(monkeypatch):
    class EmptyVectorStore:
        def similarity_search(self, question, k, filter):
            return []

    monkeypatch.setattr(rag_pipeline, "vector_store", EmptyVectorStore())

    answer, sources = rag_pipeline.query_documents(
        "Unknown?",
        "missing-document",
        "user-123",
    )

    assert answer == "I don't know based on the uploaded document."
    assert sources == []
