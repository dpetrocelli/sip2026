"""TP 3 — snippet de configuración de logging JSON para el scraper.

Este NO es un módulo completo. Es un fragmento de referencia para que
el alumno lo integre en `main.py` del scraper de TP1·P2 (Hit #4).

Objetivo: que el scraper emita logs en formato JSON (una línea = un
objeto JSON) en lugar de texto libre. Loki + Alloy promueven los campos
del JSON a labels (`level`, `producto`, `event`), lo cual hace que las
queries del cheatsheet funcionen sin tener que parsear regex en cada
panel del dashboard.

Dependencia nueva (agregar a `requirements.txt`):

    python-json-logger>=2.0.7

Salida actual del scraper (Hit #4):

    [INFO] === Scraping: 'iPhone 16 Pro Max' ===
    [INFO] 'iPhone 16 Pro Max' -> 10 resultados

Salida con este snippet:

    {"timestamp": "2026-04-26T15:42:01.123Z", "level": "INFO",
     "name": "__main__", "message": "Scraping iniciado",
     "event": "product_started", "producto": "iPhone 16 Pro Max"}
    {"timestamp": "2026-04-26T15:42:18.456Z", "level": "INFO",
     "name": "__main__", "message": "10 resultados extraidos",
     "event": "product_finished", "producto": "iPhone 16 Pro Max",
     "result_count": 10, "duration_seconds": 17.3}
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger


# ---------------------------------------------------------------------------
# 1. Setup del logger raiz — pegar esto en main.py reemplazando el
#    logging.basicConfig actual.
# ---------------------------------------------------------------------------
def setup_json_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura el logger raiz para emitir JSON a stdout.

    Llamar UNA SOLA VEZ al inicio de main(), antes de cualquier
    `logger.info(...)`. Devuelve el logger raiz para conveniencia
    (el resto del codigo usa `logging.getLogger(__name__)` como antes).
    """
    handler = logging.StreamHandler(sys.stdout)

    # JsonFormatter con campos extra:
    #   - timestamp en ISO8601 (Loki lo parsea bien y lo usa como label de tiempo).
    #   - los campos %(...)s son los standard de logging; el resto los agrega
    #     `extra={...}` en cada llamada.
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
        timestamp=True,
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    # Limpiar cualquier handler previo (basicConfig deja uno).
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    return root


# ---------------------------------------------------------------------------
# 2. Patron de uso en el codigo del scraper.
#    Ejemplo: scrape_product() del Hit #4 reescrito para emitir eventos
#    estructurados. El campo `extra` se serializa como atributos del JSON,
#    y Alloy promueve `producto` y `event` a labels Loki.
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


def scrape_product_with_structured_logging(
    driver: Any,
    query: str,
    limit: int,
) -> list[dict]:
    """Wrapper de scrape_product() del Hit #4 con logging estructurado.

    NOTA: no copiar tal cual — esto es solo el patron del logging.
    El cuerpo real (search_and_filter, collect_results) sigue igual.
    """
    import time

    start = time.monotonic()

    # Antes:    logger.info("=== Scraping: '%s' ===", query)
    # Ahora:    log estructurado con campos buscables en LogQL.
    logger.info(
        "Scraping iniciado",
        extra={
            "event": "product_started",
            "producto": query,
        },
    )

    # ... aqui va search_and_filter(driver, query) y collect_results ...
    results: list[dict] = []  # placeholder

    duration = time.monotonic() - start

    logger.info(
        "%d resultados extraidos",
        len(results),
        extra={
            "event": "product_finished",
            "producto": query,
            "result_count": len(results),
            "duration_seconds": round(duration, 3),
        },
    )

    return results


# ---------------------------------------------------------------------------
# 3. Logging de excepciones — preservar la stacktrace completa pero en JSON.
# ---------------------------------------------------------------------------
def log_exception_example(query: str) -> None:
    """Como loggear un except sin perder la stacktrace.

    `exc_info=True` hace que JsonFormatter agregue un campo `exc_info`
    con la traceback serializada. Loki la indexa entera y se ve en
    Grafana en el panel "Logs en vivo" expandiendo la linea.
    """
    try:
        raise RuntimeError("ejemplo: timeout esperando los resultados")
    except RuntimeError:
        logger.error(
            "Fallo el scraping de '%s'",
            query,
            extra={
                "event": "product_failed",
                "producto": query,
            },
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# 4. Ejemplo de salida completa (lo que veria el alumno en `kubectl logs`
#    despues de aplicar este logging y correr el scraper):
# ---------------------------------------------------------------------------
EXAMPLE_OUTPUT = """\
{"timestamp": "2026-04-26T15:42:01.123456Z", "level": "INFO", "name": "__main__", "message": "Iniciando scraper en chrome"}
{"timestamp": "2026-04-26T15:42:01.234567Z", "level": "INFO", "name": "__main__", "message": "Scraping iniciado", "event": "product_started", "producto": "bicicleta rodado 29"}
{"timestamp": "2026-04-26T15:42:15.876543Z", "level": "INFO", "name": "__main__", "message": "10 resultados extraidos", "event": "product_finished", "producto": "bicicleta rodado 29", "result_count": 10, "duration_seconds": 14.642}
{"timestamp": "2026-04-26T15:42:16.000000Z", "level": "INFO", "name": "__main__", "message": "JSON escrito: /output/bicicleta_rodado_29.json"}
{"timestamp": "2026-04-26T15:42:30.111111Z", "level": "ERROR", "name": "__main__", "message": "Fallo el scraping de 'iPhone 16 Pro Max'", "event": "product_failed", "producto": "iPhone 16 Pro Max", "exc_info": "Traceback (most recent call last):\\n  File ..."}
"""


# ---------------------------------------------------------------------------
# 5. Como el dashboard del TP 3 consume estos logs:
#
#   * Panel "% exito por producto" cruza dos queries:
#       sum by (producto) (count_over_time({...} |= "JSON escrito" [24h]))
#         -- numerador: scrapes que terminaron OK
#       sum by (producto) (count_over_time({...} | json | event="product_started" [24h]))
#         -- denominador: scrapes que arrancaron
#
#   * Panel "Distribucion de duracion" usa unwrap sobre duration_seconds
#     que viene del log "product_finished":
#       quantile_over_time(0.95, {...} | json | unwrap duration_seconds [1h])
#
#   * Panel "Errores por hora" filtra por label level promovido:
#       sum(count_over_time({namespace="ml-scraper", level="ERROR"} [1h]))
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # Demo: configurar logging y emitir 3 eventos de ejemplo.
    setup_json_logging()
    logger.info("Iniciando scraper", extra={"event": "scraper_started"})
    scrape_product_with_structured_logging(driver=None, query="bicicleta rodado 29", limit=10)
    log_exception_example(query="iPhone 16 Pro Max")
