"""Swappable AI providers. Defaults run offline; nothing here pretends to be an LLM."""
import hashlib, math, re
from .. import config

DIM = 384
_st_model = None

def embed(text: str) -> list[float]:
    if config.EMBEDDING_PROVIDER == "sentence-transformers":
        global _st_model
        from sentence_transformers import SentenceTransformer
        _st_model = _st_model or SentenceTransformer("all-MiniLM-L6-v2")
        return _st_model.encode(text, normalize_embeddings=True).tolist()
    # Offline fallback: hashed uni+bigram vectors (lexical, NOT truly semantic)
    toks = re.findall(r"[a-z0-9+#.]+", text.lower())
    vec = [0.0] * DIM
    for g in toks + [a + " " + b for a, b in zip(toks, toks[1:])]:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        vec[h % DIM] += 1 if (h >> 20) & 1 else -1
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]

def cosine(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))

def explain(facts: dict) -> dict:
    """Narrative layer only; numbers are computed elsewhere."""
    if config.LLM_PROVIDER == "anthropic":
        try:
            import anthropic, json
            msg = anthropic.Anthropic().messages.create(
                model=config.LLM_MODEL, max_tokens=500,
                messages=[{"role": "user", "content":
                    "Write a 3-sentence, honest, encouraging explanation of this job match. Use ONLY these facts, invent nothing:\n"
                    + json.dumps(facts)}])
            return {"text": msg.content[0].text, "source": "llm"}
        except Exception as e:
            facts = {**facts, "_llm_error": str(e)}
    top = ", ".join(facts["blockers"][:2]) or "none"
    return {"text": f"Your profile is {facts['score']}% aligned with this role. "
                    f"Biggest blockers: {top}. This is an automated estimate, not a guarantee.",
            "source": "template"}
