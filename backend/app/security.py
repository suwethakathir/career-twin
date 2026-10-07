import hashlib, hmac, os, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import JWT_SECRET
from .db import get_db
from .models import User

def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 240_000)
    return salt.hex() + "$" + dk.hex()

def verify_password(pw: str, stored: str) -> bool:
    salt, dk = stored.split("$")
    cand = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 240_000)
    return hmac.compare_digest(cand.hex(), dk)

def make_token(user_id: int, hours: int = 12) -> str:
    return jwt.encode({"sub": str(user_id), "exp": int(time.time()) + hours * 3600}, JWT_SECRET, "HS256")

bearer = HTTPBearer()

def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        uid = int(jwt.decode(cred.credentials, JWT_SECRET, ["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user
