"""Schemas de entrada/salida para el endpoint de sugerencias de categorización.

Diseñado según pliego_s10_sugerencias_categorizacion_v1.md.
El endpoint es lectura pura; no hay schema de creación.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


ConfidenceLevel = Literal["high", "medium", "medium-low"]
Scope = Literal["counterparty", "project", "global"]


class CategorizationSuggestionOut(BaseModel):
    """Respuesta del endpoint GET /suggestions/transaction-categorization.

    Campos nulos (category_id=None, confidence=None, source_level=5)
    indican silencio: no hay evidencia histórica suficiente para sugerir.
    """

    category_id: Optional[int] = Field(
        None,
        description="ID de la categoría sugerida; None si nivel 5 (silencio).",
    )
    subcategory_id: Optional[int] = Field(
        None,
        description="ID de la subcategoría sugerida; None si nivel 5.",
    )
    category_name: Optional[str] = Field(
        None,
        description="Nombre resuelto de la categoría (facilita UI).",
    )
    subcategory_name: Optional[str] = Field(
        None,
        description="Nombre resuelto de la subcategoría.",
    )
    confidence: Optional[ConfidenceLevel] = Field(
        None,
        description="Nivel de confianza de la sugerencia; None si silencio.",
    )
    source_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Nivel del árbol que disparó (1-4); 5 indica silencio.",
    )
    sample_count: Optional[int] = Field(
        None,
        description="Número de movimientos históricos que soportan la sugerencia.",
    )
    scope: Optional[Scope] = Field(
        None,
        description="Ámbito efectivo del matching; None si silencio.",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "category_id": 5,
                    "subcategory_id": 23,
                    "category_name": "Combustible",
                    "subcategory_name": "Grupos_Electrogenos",
                    "confidence": "high",
                    "source_level": 2,
                    "sample_count": 12,
                    "scope": "project",
                },
                {
                    "category_id": None,
                    "subcategory_id": None,
                    "category_name": None,
                    "subcategory_name": None,
                    "confidence": None,
                    "source_level": 5,
                    "sample_count": None,
                    "scope": None,
                },
            ]
        }
