"""
Rate limiting — 5 intentos de login por IP cada 10 minutos.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={
        "detail": "Demasiados intentos de acceso. Espere 10 minutos antes de reintentar."
    })
