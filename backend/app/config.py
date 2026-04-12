"""
Configuración centralizada de la aplicación.

Lee todas las variables de entorno definidas en .env y las expone como
atributos tipados. pydantic-settings valida los valores al arrancar y
lanza un error claro si falta alguna variable obligatoria.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Variables de entorno con valores por defecto para desarrollo."""

    # --- Entorno ---
    ENV: str = "development"

    # --- Base de datos ---
    POSTGRES_DB: str = "cashflow"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- JWT ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # --- Cifrado ---
    ENCRYPTION_KEY: str

    # --- Inmutabilidad ---
    EDIT_WINDOW_MINUTES: int = 15
    IMPORT_EDIT_DAYS: int = 30

    # --- Adjuntos ---
    MAX_FILE_SIZE_MB: int = 10
    MAX_TRANSACTION_FILES_MB: int = 50

    # --- CORS ---
    FRONTEND_URL: str = "https://localhost"

    # --- Red local ---
    LOCAL_NETWORK_CIDR: str = "192.168.1.0/24"

    # --- Correo ---
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    ADMIN_EMAIL: Optional[str] = None

    # --- Nodo Bata ---
    NODE_TYPE: Optional[str] = None
    MALABO_SERVER_URL: Optional[str] = None
    SYNC_INTERVAL_MINUTES: int = 15

    # --- Rate limiting ---
    LOGIN_RATE_LIMIT: str = "5/10minutes"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
