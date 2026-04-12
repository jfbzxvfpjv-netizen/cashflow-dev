"""
Servicio de sincronización Bata → Malabo.

Este módulo es el punto de entrada del contenedor sync en docker-compose.bata.yml.
Se ejecuta como proceso independiente que sincroniza periódicamente la base de datos
local de Bata contra el servidor principal de Malabo.

La implementación completa se desarrollará en el módulo M15 (Capa 3 — Resiliencia
Operativa). Por ahora el servicio arranca, registra que está activo y espera
sin consumir recursos.
"""

import time
import os
import logging

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("sync-service")


def main():
    """Bucle principal del servicio de sincronización."""
    interval = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))
    malabo_url = os.getenv("MALABO_SERVER_URL", "")

    logger.info("Servicio de sincronización Bata iniciado")
    logger.info(f"  Servidor Malabo: {malabo_url}")
    logger.info(f"  Intervalo: cada {interval} minutos")
    logger.info("  Estado: esperando implementación completa (M15 — Capa 3)")

    while True:
        # TODO M15: implementar lógica de sincronización
        time.sleep(interval * 60)


if __name__ == "__main__":
    main()
