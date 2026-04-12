"""
Modelo ImportHistory — Historial de importaciones desde Excel.
Cada registro representa una ejecución de importación completada.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ImportHistory(Base):
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delegacion = Column(String(10), nullable=False)
    filename = Column(String(255), nullable=False)
    session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=False)
    rows_imported = Column(Integer, nullable=False, default=0)
    rows_skipped = Column(Integer, nullable=False, default=0)
    projects_created = Column(Integer, nullable=False, default=0)
    works_created = Column(Integer, nullable=False, default=0)
    imported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    imported_at = Column(DateTime, server_default=func.now())
