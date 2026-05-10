# Cashflow R2i — Fingerprint Matcher Microservice

Microservicio interno de matching biométrico SourceAFIS para Caja R2i.

## Resumen

Servicio HTTP minimalista en Java que expone tres endpoints:

- `POST /extract` — extrae template biométrico desde imagen.
- `POST /match` — compara dos templates y devuelve score 0-100.
- `GET /health` — healthcheck.

Acceso solo desde la red interna Docker Compose. **No expuesto al exterior.**

## Stack

- Java 17 (Eclipse Temurin)
- Javalin 7.2.0
- SourceAFIS Java 3.18.1
- Maven 3.9 (solo para build)

## Build local sin Docker (requiere Maven y JDK 17 instalados)

```bash
cd microservices/fingermatcher
mvn clean package
java -jar target/fingermatcher-1.0.0.jar
```

## Build y ejecución con Docker

```bash
cd microservices/fingermatcher
docker build -t cashflow-fingermatcher .
docker run --rm -p 8080:8080 cashflow-fingermatcher
```

## Validación rápida con curl

```bash
# Health check (debe devolver JSON con status: ok)
curl http://localhost:8080/health

# Extract template (necesita imagen base64 — ejemplo con BMP de FVC)
IMG_B64=$(base64 -i fingerprint.bmp)
curl -X POST http://localhost:8080/extract \
  -H "Content-Type: application/json" \
  -d "{\"image_b64\":\"$IMG_B64\",\"image_format\":\"bmp\"}"

# Match dos templates (los template_b64 vienen de respuestas de /extract)
curl -X POST http://localhost:8080/match \
  -H "Content-Type: application/json" \
  -d '{"template_a_b64":"...","template_b_b64":"..."}'
```

## Variables de entorno

| Variable | Default | Función |
|---|---|---|
| `HTTP_PORT` | `8080` | Puerto interno donde escucha |
| `JAVA_OPTS` | `-Xmx256m -Xms128m` | Opciones JVM |

## Comportamiento esperado

- Extracción típica: <500 ms por imagen en hardware modesto.
- Match típico: <50 ms por par de templates.
- Memoria estable: ~150-200 MB tras warmup.

## Códigos de error

- `400` — request mal formada, base64 inválido, falta campo obligatorio.
- `422` — imagen no procesable o sin minucias suficientes.
- `500` — error inesperado interno (revisar logs).

## Especificación completa

Ver `docs/pliegos/pliego_m11_fingerprint_v1.md`.
