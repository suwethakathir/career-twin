from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Job, JobMatch, Resume, UserSkill
from ..security import current_user
from ..services import matching

router = APIRouter(prefix="/matching", tags=["matching"])

def _ctx(job_id, user, db):
    job = db.get(Job, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    resume = db.query(Resume).filter_by(user_id=user.id).order_by(Resume.id.desc()).first()
    if not resume:
        raise HTTPException(400, "Upload a resume first")
    skills = {s.skill: s.status for s in db.query(UserSkill).filter_by(user_id=user.id)}
    return job, resume, skills

@router.post("/{job_id}")
def run(job_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    job, resume, skills = _ctx(job_id, user, db)
    res = matching.match(skills, resume.parsed["years_experience"], resume.raw_text, job.parsed, job.raw_text)
    db.add(JobMatch(user_id=user.id, job_id=job.id, score=res["score"], result=res)); db.commit()
    return res

class WhatIf(BaseModel):
    add_skills: list[str]

@router.post("/{job_id}/what-if")
def what_if(job_id: int, body: WhatIf, user=Depends(current_user), db: Session = Depends(get_db)):
    job, resume, skills = _ctx(job_id, user, db)
    return matching.what_if(skills, resume.parsed["years_experience"], resume.raw_text, job.parsed, job.raw_text,
                            [s.lower() for s in body.add_skills])
