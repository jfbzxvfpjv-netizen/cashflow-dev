"""
M11 Fingerprint - Cliente del motor de matching biometrico.
Abstraccion FingerprintMatchingEngine + implementacion SourceAFISJavaEngine
que habla por HTTP con el microservicio Java fingermatcher.
"""
from abc import ABC, abstractmethod
from typing import Tuple
import base64
import os
import httpx


class FingerprintEngineError(Exception):
    """Error generico del motor de fingerprint."""
    pass


class FingerprintMatchingEngine(ABC):
    @abstractmethod
    def extract_template(self, image_bytes: bytes,
                         image_format: str = "raw_grayscale") -> Tuple[bytes, int, int]:
        """Returns (template_bytes, quality_score, minutiae_count)."""
        ...

    @abstractmethod
    def match_templates(self, template_a: bytes, template_b: bytes) -> float:
        """Returns score 0-100."""
        ...

    @abstractmethod
    def health_check(self) -> dict:
        ...


class SourceAFISJavaEngine(FingerprintMatchingEngine):
    """Cliente HTTP del microservicio Java cashflow-dev-fingermatcher."""

    def __init__(self, base_url: str = None,
                 timeout_connect: int = None,
                 timeout_read: int = None):
        self.base_url = (base_url
                         or os.getenv("FINGERPRINT_ENGINE_URL", "http://fingermatcher:8080")
                         ).rstrip("/")
        tc = timeout_connect or int(os.getenv("FINGERPRINT_ENGINE_TIMEOUT_CONNECT", "5"))
        tr = timeout_read or int(os.getenv("FINGERPRINT_ENGINE_TIMEOUT_READ", "10"))
        self.client = httpx.Client(timeout=httpx.Timeout(connect=tc, read=tr, write=tc, pool=tc))

    def extract_template(self, image_bytes, image_format="raw_grayscale"):
        try:
            response = self.client.post(
                f"{self.base_url}/extract",
                json={
                    "image_b64": base64.b64encode(image_bytes).decode("ascii"),
                    "image_format": image_format,
                },
            )
        except httpx.HTTPError as e:
            raise FingerprintEngineError(f"Engine connection failed: {e}")

        if response.status_code == 422:
            data = response.json()
            raise FingerprintEngineError(
                f"Image not processable (minutiae={data.get('minutiae_count', 0)}): "
                f"{data.get('error', 'unknown')}"
            )
        if response.status_code != 200:
            raise FingerprintEngineError(
                f"Engine extract failed: {response.status_code} - {response.text}")

        data = response.json()
        return (
            base64.b64decode(data["template_b64"]),
            data["quality_score"],
            data["minutiae_count"],
        )

    def match_templates(self, template_a, template_b):
        try:
            response = self.client.post(
                f"{self.base_url}/match",
                json={
                    "template_a_b64": base64.b64encode(template_a).decode("ascii"),
                    "template_b_b64": base64.b64encode(template_b).decode("ascii"),
                },
            )
        except httpx.HTTPError as e:
            raise FingerprintEngineError(f"Engine connection failed: {e}")

        if response.status_code != 200:
            raise FingerprintEngineError(
                f"Engine match failed: {response.status_code} - {response.text}")

        return float(response.json()["score"])

    def health_check(self):
        try:
            response = self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise FingerprintEngineError(f"Engine health check failed: {e}")


# Singleton para reuso del cliente HTTP (con su pool de conexiones)
_default_engine: SourceAFISJavaEngine = None


def get_engine() -> FingerprintMatchingEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = SourceAFISJavaEngine()
    return _default_engine
