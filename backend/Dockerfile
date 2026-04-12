# ============================================================================
# Dockerfile — Backend (Python 3.11 + FastAPI)
# ============================================================================
# Imagen base python:3.11-slim compatible con ARM64 y x86-64 de forma nativa.
# No incluir instrucciones específicas de arquitectura — Docker selecciona
# automáticamente la variante correcta según la plataforma del host.
# ============================================================================

FROM python:3.11-slim

# --- Metadatos ---
LABEL maintainer="R2iNetwork"
LABEL description="Backend Gestión Flujo de Caja — FastAPI + Uvicorn"

# --- Dependencias del sistema ---
# WeasyPrint requiere librerías de renderizado para la generación de PDF.
# libpq-dev es necesario para psycopg2 (driver PostgreSQL).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    shared-mime-info \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# --- Directorio de trabajo ---
WORKDIR /app

# --- Dependencias Python (capa cacheada) ---
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Código fuente ---
COPY . .

# --- Directorio de uploads con permisos ---
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# --- Puerto de Uvicorn ---
EXPOSE 8000

# --- Comando de arranque ---
# --host 0.0.0.0 para aceptar conexiones del proxy Nginx
# --reload activo en desarrollo, desactivado en producción vía variable de entorno
CMD ["sh", "-c", "\
    LOG=$(echo ${LOG_LEVEL:-info} | tr 'A-Z' 'a-z') && \
    if [ \"$ENV\" = 'development' ]; then \
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level $LOG; \
    else \
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level $LOG; \
    fi \
"]
