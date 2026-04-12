#!/bin/bash
# ============================================================================
# Generador de certificado TLS autofirmado para desarrollo
# ============================================================================
# Genera un certificado autofirmado válido por 365 días en nginx/ssl/.
# Ejecutar una sola vez antes del primer docker compose up.
#
# Uso:
#   chmod +x scripts/generate-ssl.sh
#   ./scripts/generate-ssl.sh
#
# En producción usar Let's Encrypt en su lugar:
#   certbot certonly --standalone -d <dominio>
#   Copiar fullchain.pem → nginx/ssl/cert.pem
#   Copiar privkey.pem  → nginx/ssl/key.pem
# ============================================================================

set -e

SSL_DIR="$(cd "$(dirname "$0")/.." && pwd)/nginx/ssl"
mkdir -p "$SSL_DIR"

if [ -f "$SSL_DIR/cert.pem" ] && [ -f "$SSL_DIR/key.pem" ]; then
    echo "[INFO] Los certificados ya existen en $SSL_DIR"
    echo "       Elimínalos manualmente si quieres regenerarlos."
    exit 0
fi

echo "[INFO] Generando certificado TLS autofirmado para desarrollo..."

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/C=GQ/ST=Litoral/L=Bata/O=R2iNetwork/OU=Desarrollo/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "[OK] Certificado generado en:"
echo "     Certificado: $SSL_DIR/cert.pem"
echo "     Clave:       $SSL_DIR/key.pem"
echo ""
echo "     En el navegador, aceptar el certificado autofirmado al acceder a https://localhost"
