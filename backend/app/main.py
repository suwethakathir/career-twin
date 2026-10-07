import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import config, models  # noqa
from .db import Base, engine
from .routers import auth, resumes, jobs, matching

logging.basicConfig(level=logging.INFO)
Base.metadata.create_all(engine)
app = FastAPI(title="AI Career Intelligence Platform", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
for r in (auth, resumes, jobs, matching):
    app.include_router(r.router)

@app.get("/health")
def health():
    return {"ok": True, "embedding": config.EMBEDDING_PROVIDER, "llm": config.LLM_PROVIDER}
