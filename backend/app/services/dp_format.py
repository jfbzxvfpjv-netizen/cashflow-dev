"""
M11 Fingerprint - Conversor del formato propietario DigitalPersona Raw a PNG.

El SDK @digitalpersona/devices con SampleFormat.Raw devuelve un objeto JSON
anidado por cada evento SamplesAcquired. El frontend extrae el campo .Data
del objeto y lo envia al backend en image_b64. Este modulo detecta esa
estructura, decodifica el bitmap interno y reconstruye un PNG estandar que
SourceAFIS pueda procesar.

Estructura del envelope DP:
  base64(JSON {
    "Compression": 0,
    "Data": base64url(<bitmap bytes>)
  })

Asumimos 357x392 a 8bpp grayscale (estandar del U.are.U 4500 a 500 DPI).
Si el bitmap tiene cabecera al inicio, los ultimos 357*392=139944 bytes
son los pixeles. El resto (cabecera DP propietaria) se descarta.

Si el input no es DP-Raw, la funcion devuelve None y el caller mantiene el
flujo original con base64 standard (PNG estandar, casos de test, etc).
"""
import base64
import io
import json
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Dimensiones conocidas indexadas por tamano del bitmap (width*height bytes).
# El bitmap DigitalPersona Raw viene sin cabecera embebida; los bytes son
# directamente pixeles grayscale 8bpp. Auto-deteccion por tamano:
KNOWN_DIMENSIONS = {
    115200: (320, 360),   # U.are.U 4500 + ADC 5.2 (validado en Malabo)
    139944: (357, 392),   # U.are.U 4500 nominal a 500 DPI
    73728:  (256, 288),   # Configuracion alternativa U.are.U
    102400: (320, 320),   # Cuadrado
    115456: (368, 320),   # Variante observada
}

# Fallback si el tamano no esta en KNOWN_DIMENSIONS
DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 360


def _b64url_decode(s: str) -> bytes:
    """Decodifica base64 estandar o base64Url, anadiendo padding si falta."""
    rem = len(s) % 4
    if rem:
        s = s + '=' * (4 - rem)
    return base64.urlsafe_b64decode(s)


def try_convert_dp_to_png(image_b64: str) -> Optional[bytes]:
    """Detecta envelope DigitalPersona Raw y lo convierte a PNG.

    Args:
        image_b64: contenido del campo image_b64 del request.

    Returns:
        bytes del PNG si el input era DP-Raw; None en otro caso (caller
        debe procesar image_b64 como PNG estandar via base64.b64decode).
    """
    if not isinstance(image_b64, str) or len(image_b64) < 50:
        return None

    # Decodificar envelope externo y verificar que es JSON con keys DP
    try:
        decoded = _b64url_decode(image_b64)
        text = decoded.decode('utf-8')
        envelope = json.loads(text)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(envelope, dict):
        return None
    if 'Compression' not in envelope or 'Data' not in envelope:
        return None

    compression = envelope.get('Compression', 0)
    if compression != 0:
        logger.warning(f"DP-Raw compression={compression} no soportada todavia")
        return None

    try:
        bitmap_bytes = _b64url_decode(envelope['Data'])
    except Exception as e:
        logger.warning(f"DP-Raw Data interno no decodificable: {e}")
        return None

    bitmap_size = len(bitmap_bytes)

    # Auto-deteccion: si el tamano coincide con una combinacion conocida, usarla
    if bitmap_size in KNOWN_DIMENSIONS:
        width, height = KNOWN_DIMENSIONS[bitmap_size]
        logger.info(
            f"DP-Raw dimensiones auto-detectadas por tamano "
            f"({bitmap_size} bytes -> {width}x{height})"
        )
    else:
        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
        expected = width * height
        if bitmap_size < expected:
            logger.warning(
                f"DP-Raw bitmap insuficiente: {bitmap_size} bytes, "
                f"esperados al menos {expected} ({width}x{height}@8bpp). "
                f"Anade tu combinacion a KNOWN_DIMENSIONS si es nueva."
            )
            return None

    expected = width * height
    # Los ultimos width*height bytes son los pixeles, el resto (si hay) cabecera DP
    pixel_bytes = bitmap_bytes[-expected:]

    try:
        img = Image.frombytes('L', (width, height), pixel_bytes)
        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=False)
        png_bytes = buf.getvalue()
        logger.info(
            f"DP-Raw {width}x{height} convertido a PNG: "
            f"bitmap_total={bitmap_size}B, pixels={len(pixel_bytes)}B, png={len(png_bytes)}B"
        )
        return png_bytes
    except Exception as e:
        logger.warning(f"DP-Raw conversion fallida en PIL: {e}")
        return None
