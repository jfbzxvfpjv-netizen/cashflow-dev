"""
Servicio de autenticación — Login, logout y audit_log.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import verify_password, create_access_token, detect_access_type
from app.config import settings


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def login_user(db: Session, user: User, client_ip: str) -> dict:
    user.last_login = datetime.now(timezone.utc)
    db.flush()

    access_token = create_access_token(
        user_id=user.id, username=user.username,
        role=user.role, delegacion=user.delegacion,
    )

    access_type = detect_access_type(client_ip)
    db.add(AuditLog(
        user_id=user.id,
        delegacion=user.delegacion if user.delegacion != "Ambas" else None,
        action="LOGIN", entity="users", entity_id=user.id,
        details={"username": user.username, "access_type": access_type},
        ip_address=client_ip, access_type=access_type,
    ))
    db.commit()

    return {
        "access_token": access_token, "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600, "user": user,
    }


def logout_user(db: Session, user: User, client_ip: str) -> None:
    access_type = detect_access_type(client_ip)
    db.add(AuditLog(
        user_id=user.id,
        delegacion=user.delegacion if user.delegacion != "Ambas" else None,
        action="LOGOUT", entity="users", entity_id=user.id,
        details={"username": user.username},
        ip_address=client_ip, access_type=access_type,
    ))
    db.commit()


def log_failed_login(db: Session, username: str, client_ip: str) -> None:
    access_type = detect_access_type(client_ip)
    db.add(AuditLog(
        user_id=None, delegacion=None,
        action="LOGIN_FAILED", entity="users", entity_id=None,
        details={"username_attempted": username},
        ip_address=client_ip, access_type=access_type,
    ))
    db.commit()
