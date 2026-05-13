from fastapi import FastAPI

app = FastAPI(title="Czanix RAG Pipeline", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/v1/ask")
async def ask(query: str):
    """RAG endpoint — configure providers in .env"""
    return {"message": "Configure embedding/llm providers in .env to enable RAG"}
