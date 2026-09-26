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


def ingest_pdf(file_path: str) -> int:
    chunks = chunk_pdf(file_path)
    vector_store.add_documents(chunks)
    return len(chunks)

def query_documents(question: str, k: int = 4) -> str:
    documents = vector_store.similarity_search(question, k=k)

    context = "\n\n".join(
        document.page_content for document in documents
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return response.content