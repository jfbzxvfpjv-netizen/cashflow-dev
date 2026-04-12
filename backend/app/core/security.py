"""
Módulo de seguridad — Hash de contraseñas, JWT y detección de acceso remoto.
"""
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    user_id: int, username: str, role: str, delegacion: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS))
    payload = {
        "sub": str(user_id), "username": username,
        "role": role, "delegacion": delegacion,
        "exp": expire, "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        return None

def detect_access_type(client_ip: str) -> str:
    try:
        client = ipaddress.ip_address(client_ip)
        local_cidrs = [c.strip() for c in settings.LOCAL_NETWORK_CIDR.split(",")]
        networks = [ipaddress.ip_network(c, strict=False) for c in local_cidrs]
        return "local" if any(client in net for net in networks) else "remote"
    except ValueError:
        return "remote"

def validate_password_policy(password: str) -> list[str]:
    errors = []
    if len(password) < 8:
        errors.append("La contrasena debe tener al menos 8 caracteres.")
    if not any(c.isupper() for c in password):
        errors.append("La contrasena debe contener al menos una letra mayuscula.")
    if not any(c.isdigit() for c in password):
        errors.append("La contrasena debe contener al menos un numero.")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,./<>?" for c in password):
        errors.append("La contrasena debe contener al menos un caracter especial.")
    return errors
