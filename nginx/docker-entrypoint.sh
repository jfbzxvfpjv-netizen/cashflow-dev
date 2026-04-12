#!/bin/sh
# ============================================================================
# Entrypoint Nginx — genera certificado autofirmado si no existe
# ============================================================================
# En desarrollo: genera un certificado autofirmado automáticamente.
# En producción: los certificados de Let's Encrypt deben estar montados
# en /etc/nginx/ssl/ antes de arrancar.
# ============================================================================

set -e

SSL_DIR="/etc/nginx/ssl"

if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "[nginx-entrypoint] Certificados TLS no encontrados. Generando autofirmado..."
    apk add --no-cache openssl > /dev/null 2>&1
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=GQ/ST=Litoral/L=Bata/O=R2iNetwork/OU=Dev/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
        2>/dev/null
    echo "[nginx-entrypoint] Certificado autofirmado generado en $SSL_DIR"
else
    echo "[nginx-entrypoint] Certificados TLS encontrados."
fi

echo "[nginx-entrypoint] Arrancando Nginx..."
exec nginx -g "daemon off;"
