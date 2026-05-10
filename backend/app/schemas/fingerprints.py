"""
M11 Fingerprint - Schemas Pydantic para endpoints REST.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QualityRequest(BaseModel):
    image_b64: str
    image_format: str = "raw_grayscale"


class QualityResponse(BaseModel):
    quality_score: int
    minutiae_count: int
    has_minutiae: bool


class EnrollRequest(BaseModel):
    employee_id: int
    finger_position: str
    images_b64: List[str] = Field(..., min_length=4, max_length=4,
                                   description="Exactamente 4 imagenes base64 del mismo dedo")


class EnrolledCapture(BaseModel):
    capture_index: int
    quality_score: int


class EnrollResponse(BaseModel):
    employee_id: int
    finger_position: str
    enrolled: List[EnrolledCapture]


class VerifyRequest(BaseModel):
    employee_id: int
    image_b64: str


class VerifyResponse(BaseModel):
    matched: bool
    score: float
    finger_position: Optional[str] = None
    threshold: int


class FingerprintMetadata(BaseModel):
    id: int
    finger_position: str
    capture_index: int
    quality_score: Optional[int] = None
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class EmployeeFingerprintsResponse(BaseModel):
    employee_id: int
    employee_name: str
    fingerprints: List[FingerprintMetadata]
    total_captures: int


class EmployeeWithEnrollment(BaseModel):
    employee_id: int
    full_name: str
    delegacion: str
    user_id: Optional[int] = None
    capture_count: int
    fingers_enrolled: List[str]


class EnginStatusResponse(BaseModel):
    healthy: bool
    version: Optional[str] = None
    engine: Optional[str] = None
    uptime_seconds: Optional[int] = None
    error: Optional[str] = None


class SignatureMethodResponse(BaseModel):
    method: str  # wacom | fingerprint | wacom_only_no_enrollment
    signer_name: str
    employee_id: Optional[int] = None
    has_enrollment: bool
    fallback_method: Optional[str] = None
