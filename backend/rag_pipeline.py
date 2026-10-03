import os

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is not set in the environment")

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="docuquery_chunks",
    connection=database_url,
)

llm = ChatOllama(model="llama3.2")

prompt = ChatPromptTemplate.from_template(
    """
Answer the question based only on the following context.
If the answer isn't in the context, say you don't know.

Context:
{context}

Question:
{question}
"""
)

def chunk_pdf(file_path: str) -> list[Document]:
    pages = PyPDFLoader(file_path).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    return splitter.split_documents(pages)


def ingest_pdf(file_path: str, document_id: str, filename: str) -> int:
    chunks = chunk_pdf(file_path)

    for chunk in chunks:
        page_number = chunk.metadata.get("page", 0) + 1
        chunk.metadata.update(
            {
                "document_id": document_id,
                "filename": filename,
                "page_number": page_number,
                "source": filename,
            }
        )

    vector_store.add_documents(chunks)
    return len(chunks)

def query_documents(question: str, document_id: str, k: int = 4) -> tuple[str, list[dict]]:
    documents = vector_store.similarity_search(
        question,
        k=k,
        filter={"document_id": document_id},
    )

    if not documents:
        return "I don't know based on the uploaded document.", []

    context = "\n\n".join(
        (
            f"[Source: {document.metadata.get('filename', 'unknown')}, "
            f"page {document.metadata.get('page_number', 'unknown')}]\n"
            f"{document.page_content}"
        )
        for document in documents
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    source_items = []
    seen_sources = set()

    for document in documents:
        source = {
            "filename": document.metadata.get("filename", "unknown"),
            "page": document.metadata.get("page_number"),
        }
        source_key = (source["filename"], source["page"])
        if source_key not in seen_sources:
            source_items.append(source)
            seen_sources.add(source_key)

    return response.content, source_items
