from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from ..config import MAX_UPLOAD_BYTES
from ..db import get_db
from ..models import Resume, UserSkill
from ..security import current_user
from ..services.parser import extract_text, parse_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("/upload")
async def upload(file: UploadFile, user=Depends(current_user), db: Session = Depends(get_db)):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (5MB max)")
    try:
        text = extract_text(file.filename or "", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if len(text.strip()) < 30:
        raise HTTPException(422, "Could not extract readable text")
    parsed = parse_resume(text)
    r = Resume(user_id=user.id, filename=(file.filename or "resume")[:255], raw_text=text, parsed=parsed)
    db.add(r); db.flush()
    db.query(UserSkill).filter_by(user_id=user.id).delete()
    for s in parsed["skill_evidence"]:
        db.add(UserSkill(user_id=user.id, resume_id=r.id, skill=s["skill"], status=s["status"],
                         confidence=s["confidence"], evidence=s["evidence"]))
    db.commit()
    return {"resume_id": r.id, "parsed": {k: v for k, v in parsed.items() if k != "sections"}}

@router.get("/skills")
def my_skills(user=Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(UserSkill).filter_by(user_id=user.id).all()
    return [{"skill": s.skill, "status": s.status, "confidence": s.confidence, "evidence": s.evidence} for s in rows]

@router.delete("/{resume_id}")
def delete(resume_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(Resume, resume_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.query(UserSkill).filter_by(resume_id=r.id).delete()
    db.delete(r); db.commit()
    return {"deleted": True}
