from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Job
from ..security import current_user
from ..services.parser import parse_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

class JobIn(BaseModel):
    title: str = Field(max_length=255)
    description: str = Field(min_length=20, max_length=20000)

@router.post("/analyze")
def analyze(j: JobIn, user=Depends(current_user), db: Session = Depends(get_db)):
    job = Job(user_id=user.id, title=j.title, raw_text=j.description, parsed=parse_job(j.description))
    db.add(job); db.commit()
    return {"job_id": job.id, "parsed": job.parsed}

@router.get("")
def list_jobs(user=Depends(current_user), db: Session = Depends(get_db)):
    return [{"job_id": j.id, "title": j.title, "parsed": j.parsed} for j in db.query(Job).filter_by(user_id=user.id)]
