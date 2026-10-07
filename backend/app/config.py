import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./career.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "hash")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "template")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
