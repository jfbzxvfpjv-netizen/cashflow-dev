"""
Router de autenticación — /api/v1/auth
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserBasicResponse, LogoutResponse
from app.services.auth_service import authenticate_user, login_user, logout_user, log_failed_login
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/10minutes")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        log_failed_login(db, body.username, _get_client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"})
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario desactivada.")

    result = login_user(db, user, _get_client_ip(request))
    return TokenResponse(
        access_token=result["access_token"], token_type=result["token_type"],
        expires_in=result["expires_in"],
        user=UserBasicResponse.model_validate(result["user"]),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    logout_user(db, current_user, _get_client_ip(request))
    return LogoutResponse()


@router.get("/me", response_model=UserBasicResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserBasicResponse.model_validate(current_user)
