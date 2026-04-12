"""
Dependencias FastAPI — JWT, RBAC y detección de acceso local/remoto.
"""
from typing import Callable
import ipaddress

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    user = db.query(User).get(user_id)
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o desactivado")
    return user


def require_role(*allowed_roles: str) -> Callable:
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Roles permitidos: {', '.join(allowed_roles)}"
            )
        return current_user
    return checker


def detect_access_type(request: Request) -> str:
    client_ip = request.client.host if request.client else "0.0.0.0"
    try:
        cidrs = [c.strip() for c in settings.LOCAL_NETWORK_CIDR.split(",")]
        networks = [ipaddress.ip_network(c, strict=False) for c in cidrs]
        addr = ipaddress.ip_address(client_ip)
        return "local" if addr in network or client_ip in ("127.0.0.1", "::1") else "remote"
    except ValueError:
        return "remote"
