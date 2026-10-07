import io, re
from .skills import extract_skills

ALLOWED = {".pdf", ".docx", ".txt"}
SECTION_MAP = {"education": "education", "skills": "skills", "technical skills": "skills", "project": "projects",
               "projects": "projects", "experience": "experience", "work experience": "experience",
               "internship": "experience", "internships": "experience", "certification": "certifications",
               "certifications": "certifications", "achievements": "achievements", "summary": "summary"}
HEAD = re.compile(r"^\s*([A-Za-z ]{4,25}?)\s*:?\s*$")
EVIDENCE_SECTIONS = ["projects", "experience", "certifications", "achievements"]

def extract_text(filename: str, data: bytes) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise ValueError("Only PDF, DOCX, TXT allowed")
    if ext == ".pdf":
        if not data.startswith(b"%PDF"):
            raise ValueError("File is not a valid PDF")
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    if ext == ".docx":
        if not data.startswith(b"PK"):
            raise ValueError("File is not a valid DOCX")
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")

def split_sections(text: str) -> dict[str, str]:
    secs: dict[str, list] = {"header": []}
    cur = "header"
    for line in text.splitlines():
        m = HEAD.match(line)
        if m and m.group(1).strip().lower() in SECTION_MAP:
            cur = SECTION_MAP[m.group(1).strip().lower()]
            secs.setdefault(cur, [])
        else:
            secs[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in secs.items()}

def estimate_years(text: str, secs: dict) -> float:
    found = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text, re.I)]
    if found:
        return max(found)
    return 0.5 if secs.get("experience") else 0.0   # heuristic: internship-level

def classify_skills(secs: dict) -> list[dict]:
    listed = extract_skills(secs.get("skills", ""))
    counts = {s: {} for s in extract_skills("\n".join(secs.values()))}
    for sec in EVIDENCE_SECTIONS:
        for s, n in extract_skills(secs.get(sec, "")).items():
            counts.setdefault(s, {})[sec] = n
    out = []
    for s, where in counts.items():
        n = sum(where.values())
        status = "proven" if (len(where) >= 2 or n >= 3) else "claimed" if n >= 1 else "insufficient_evidence"
        out.append({"skill": s, "status": status, "confidence": round(min(0.9, 0.25 + 0.2 * n), 2),
                    "listed_in_skills": s in listed, "evidence": where})
    return sorted(out, key=lambda x: -x["confidence"])

def parse_resume(text: str) -> dict:
    secs = split_sections(text)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"\+?\d[\d\s-]{8,13}\d", text)
    first = next((l.strip() for l in text.splitlines() if l.strip()), "")
    cgpa = re.search(r"(?:cgpa|gpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)", text, re.I)
    return {"name": first[:80], "email": email.group(0) if email else None, "phone": phone.group(0) if phone else None,
            "cgpa": float(cgpa.group(1)) if cgpa else None, "sections": secs,
            "projects": [l.strip("-• ").strip() for l in secs.get("projects", "").splitlines() if l.strip()],
            "years_experience": estimate_years(text, secs), "skill_evidence": classify_skills(secs)}

def parse_job(text: str) -> dict:
    low = text.lower()
    m = re.search(r"(preferred|nice to have|good to have|bonus|plus)", low)
    req_txt, pref_txt = (text[:m.start()], text[m.start():]) if m else (text, "")
    req = extract_skills(req_txt)
    pref = {k: v for k, v in extract_skills(pref_txt).items() if k not in req}
    yrs = re.search(r"(\d+)\s*\+?\s*years?", low)
    sal = re.search(r"(?:₹|rs\.?|inr|\$)\s?[\d.,]+\s*(?:lpa|k|lakhs?)?(?:\s*[-–to]+\s*[\d.,]+\s*(?:lpa|k|lakhs?)?)?", low)
    return {"required_skills": sorted(req), "preferred_skills": sorted(pref),
            "min_years": int(yrs.group(1)) if yrs else 0,
            "work_mode": next((w for w in ("remote", "hybrid", "onsite", "on-site") if w in low), None),
            "salary_text": sal.group(0) if sal else None}
