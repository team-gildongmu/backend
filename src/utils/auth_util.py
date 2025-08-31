from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_utils import decode_token


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials and credentials.scheme == "Bearer":
            payload = decode_token(credentials.credentials)
            if payload:
                return payload  # ✅ return decoded payload
            else:
                raise HTTPException(status_code=403, detail="Invalid or expired token.")
        raise HTTPException(status_code=403, detail="Invalid authorization code.")


async def get_refresh_token_from_cookie(request: Request) -> str | None:
    cookies = request.cookies
    if not cookies:
        return None
    return cookies.get("refresh-token")