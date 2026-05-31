import os
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
import bcrypt

# Per produzione, SECRET_KEY deve essere presa dalle variabili d'ambiente
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b3a5b3a3c1e2f9d8b7a6c5e4f3d2e1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6c5e4")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days per comodità

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
