"""
Configuración centralizada — Variables de entorno.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/cashflow"
    POSTGRES_PASSWORD: str = "postgres"
    JWT_SECRET: str = "dev-secret-change-in-production-min-32-chars!!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    FRONTEND_URL: str = "https://localhost"
    LOCAL_NETWORK_CIDR: str = "192.168.1.0/24"
    ENCRYPTION_KEY: str = "dev-encryption-key-change-in-prod!!"
    MAX_FILE_SIZE_MB: int = 10
    MAX_TRANSACTION_FILES_MB: int = 50
    EDIT_WINDOW_MINUTES: int = 15
    IMPORT_EDIT_DAYS: int = 30
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ADMIN_EMAIL: str = ""
    SYNC_INTERVAL_MINUTES: int = 15

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
