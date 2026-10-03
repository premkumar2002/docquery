from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router


app = FastAPI(
    title="DocuQuery API",
    description="Document ingestion and grounded question answering API.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
