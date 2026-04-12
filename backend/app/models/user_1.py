"""
Modelo User — Tabla users.

Define los cuatro perfiles del sistema (admin, contable, gestor, consulta)
con campo delegación y soporte preparado para 2FA (Capa 2).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY, func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # admin, contable, gestor, consulta
    delegacion = Column(String(10), nullable=False)  # Bata, Malabo, Ambas
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    totp_recovery_codes = Column(ARRAY(String), nullable=True)
    active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<User {self.username} ({self.role}/{self.delegacion})>"
