import os


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://docuquery:devpassword@localhost:5432/docuquery",
)
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
