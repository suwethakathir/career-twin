from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..security import hash_password, verify_password, make_token

router = APIRouter(prefix="/auth", tags=["auth"])

class Creds(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

@router.post("/register")
def register(c: Creds, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=c.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    u = User(email=c.email.lower(), hashed_password=hash_password(c.password))
    db.add(u); db.commit()
    return {"access_token": make_token(u.id), "token_type": "bearer"}

@router.post("/login")
def login(c: Creds, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=c.email.lower()).first()
    if not u or not verify_password(c.password, u.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": make_token(u.id), "token_type": "bearer"}
