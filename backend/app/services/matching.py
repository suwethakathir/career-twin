"""Transparent hybrid score. LLM never produces numbers.
Only job-relevant inputs are accepted: skills+status, years, resume text. No gender/age/photo/etc."""
from .skills import similarity, PREREQ
from .providers import embed, cosine, explain

W = {"proven": 1.0, "verified": 1.0, "claimed": 0.7, "insufficient_evidence": 0.4}
WEIGHTS = {"technical": 0.6, "semantic": 0.2, "experience": 0.2}

def assess(req: str, user: dict[str, str]) -> dict:
    if req in user:
        st = user[req]
        label = {"proven": "strong", "verified": "strong", "claimed": "basic"}.get(st, "unverified")
        return {"skill": req, "label": label, "coverage": W[st], "note": f"{st.replace('_', ' ')}"}
    best, via = 0.0, None
    for u, st in user.items():
        c = similarity(req, u) * W[st]
        if c > best:
            best, via = c, u
    if best > 0:
        return {"skill": req, "label": "adjacent", "coverage": best, "note": f"transferable from {via}"}
    return {"skill": req, "label": "missing", "coverage": 0.0, "note": "no evidence found"}

def order_gaps(gaps: list[dict]) -> list[str]:
    names = [g["skill"] for g in sorted(gaps, key=lambda g: -g["priority"])]
    out: list[str] = []
    for s in names:
        for p in PREREQ.get(s, []):
            if p in names and p not in out:
                out.append(p)
        if s not in out:
            out.append(s)
    return out

def compute(user: dict[str, str], years: float, resume_text: str, job: dict, job_text: str) -> dict:
    req = [assess(s, user) for s in job["required_skills"]]
    pref = [assess(s, user) for s in job["preferred_skills"]]
    den = len(req) + 0.5 * len(pref)
    tech = (sum(a["coverage"] for a in req) + 0.5 * sum(a["coverage"] for a in pref)) / den if den else 0.5
    sem = max(0.0, min(1.0, cosine(embed(resume_text), embed(job_text)) * 2))
    exp = 1.0 if not job["min_years"] else min(1.0, years / job["min_years"])
    score = round(100 * (WEIGHTS["technical"] * tech + WEIGHTS["semantic"] * sem + WEIGHTS["experience"] * exp))
    gaps = [{**a, "priority": (2 if a in req else 1) * (1.0 if a["label"] == "missing" else 0.5)}
            for a in req + pref if a["label"] in ("missing", "unverified", "adjacent")]
    order = order_gaps(gaps)
    return {"score": score,
            "breakdown": {"technical": round(tech * 100), "semantic_similarity": round(sem * 100), "experience": round(exp * 100)},
            "weights": WEIGHTS, "why_not_me": {"required": req, "preferred": pref},
            "recommended_learning_order": order}

def match(user, years, resume_text, job, job_text) -> dict:
    r = compute(user, years, resume_text, job, job_text)
    r["explanation"] = explain({"score": r["score"], "blockers": r["recommended_learning_order"]})
    r["disclaimer"] = "AI estimate based on stated evidence; not a prediction or guarantee."
    return r

def what_if(user, years, resume_text, job, job_text, add: list[str]) -> dict:
    before = compute(user, years, resume_text, job, job_text)["score"]
    steps, cur, prog = [], dict(user), before
    for s in add:
        cur[s] = "proven"  # hypothetical: assumes skill is learned AND demonstrated
        now = compute(cur, years, resume_text, job, job_text)["score"]
        steps.append({"add": s, "score": now, "delta": now - prog}); prog = now
    return {"current": before, "steps": steps, "hypothetical": True}
