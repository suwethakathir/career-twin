# AI Career Intelligence Platform (backend, slices 1-3)

Resume -> evidence-classified skills (Career Twin seed) -> job parsing -> transparent hybrid match,
"Why Not Me?", ordered skill gaps, What-If simulator.

## Run
    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env && uvicorn app.main:app --reload
    # docs: http://localhost:8000/docs      tests: pytest
    # Postgres: docker compose up --build

## Demo (Swagger UI)
1. POST /auth/register  -> Authorize with the token
2. POST /resumes/upload with seed/sample_resume.txt
3. POST /jobs/analyze with seed/sample_job.txt contents
4. POST /matching/{job_id}, then /matching/{job_id}/what-if {"add_skills":["aws"]}

## Honest status
- Embeddings default to an offline hashed-ngram vector (lexical, not truly semantic). Set
  EMBEDDING_PROVIDER=sentence-transformers for real semantic similarity.
- Explanations are templated unless LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY. Scores never come from an LLM.
- Embeddings are not yet stored in pgvector; the matcher computes them on the fly. Skill graph is a small seed.
- Not yet built: rate limiting, roles, assessments, interviews, Career DNA, scam/duplicate/salary modules,
  Career Passport, frontend.
- Score weights (60% skills / 20% semantic / 20% experience) are my starting heuristics, not validated.
