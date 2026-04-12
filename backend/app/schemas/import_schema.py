"""
Schemas para el módulo de importación desde Excel.
Cubren la validación, ejecución e historial de importaciones.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RowError(BaseModel):
    row: int
    field: str
    error: str
    value: Optional[str] = None


class ValidationSummary(BaseModel):
    total_rows: int
    valid_rows: int
    error_rows: int
    duplicate_rows: int
    projects_to_create: List[str]
    works_to_create: List[str]
    errors: List[RowError]
    can_import: bool


class ImportResult(BaseModel):
    rows_imported: int
    rows_skipped: int
    projects_created: int
    works_created: int
    session_id: int
    import_id: int


class ImportHistoryOut(BaseModel):
    id: int
    delegacion: str
    filename: str
    session_id: int
    rows_imported: int
    rows_skipped: int
    projects_created: int
    works_created: int
    imported_by: int
    imported_at: datetime

    class Config:
        from_attributes = True
