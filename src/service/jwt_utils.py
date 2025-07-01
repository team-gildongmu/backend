import python_jwt as jwt
from datetime import timedelta
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int, email: str) -> str:
    payload = {"user_id": user_id, "email": email}
    lifetime = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.generate_jwt(payload, SECRET_KEY, ALGORITHM, lifetime=lifetime)
    return token

def create_refresh_token(user_id: int, email: str) -> str:
    payload = {"user_id": user_id, "email": email}
    lifetime = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token = jwt.generate_jwt(payload, SECRET_KEY, ALGORITHM, lifetime=lifetime)
    return token

def decode_token(token: str):
    try:
        header, claims = jwt.verify_jwt(token, SECRET_KEY, [ALGORITHM])
        return claims
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None 