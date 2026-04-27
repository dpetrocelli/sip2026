"""Writer de resultados del scraper hacia PostgreSQL — Hit #8 (skeleton).

Este módulo es la capa de persistencia del histórico de scraping. Encapsula:
    - Conexión al cluster Postgres desplegado en `hit8/k8s/`.
    - Connection pool simple via `psycopg_pool.ConnectionPool`.
    - Inserción batch de los items extraídos por scrape de un producto.
    - Retries con backoff exponencial sobre errores transitorios de red/DB.

Contrato:
    >>> writer = PostgresWriter(dsn="postgresql://scraper:***@postgres:5432/scraper")
    >>> n = writer.insert_results(
    ...     producto="Bicicleta rodado 29",
    ...     items=[
    ...         {
    ...             "titulo": "Bicicleta MTB R29",
    ...             "precio": 350000.00,
    ...             "link": "https://articulo.mercadolibre.com.ar/...",
    ...             "tienda_oficial": "Bianchi Oficial",
    ...             "envio_gratis": True,
    ...             "cuotas_sin_interes": "12 cuotas sin interés",
    ...         },
    ...         ...
    ...     ],
    ... )
    >>> print(f"Insertados {n} resultados en scrape_results")

`scraped_at` se llena automáticamente con `NOW()` del lado de la base — no se
manda desde Python para evitar drift de reloj entre nodos del cluster.

Las claves del dict de items que NO matchean columnas del schema se ignoran
silenciosamente. Las claves del schema que faltan en el dict se insertan como
NULL. Esto deja margen para que el scraper agregue campos sin romper el
writer (ni viceversa) durante el desarrollo del Hit #8 por parte del alumno.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Reutilizamos el decorador de retries del Hit #5 (mismo patrón de backoff
# exponencial). El import relativo asume que ambos módulos viven bajo el mismo
# package `reference/`. En un proyecto real esto sería un package compartido.
from hit5.retry import with_backoff

logger = logging.getLogger(__name__)

# Columnas que aceptamos del dict de items. Cualquier otra clave se descarta.
# El orden importa: lo usamos para construir el statement de INSERT.
_ITEM_COLUMNS: tuple[str, ...] = (
    "titulo",
    "precio",
    "link",
    "tienda_oficial",
    "envio_gratis",
    "cuotas_sin_interes",
)

# Excepciones de psycopg que tienen sentido reintentar (red caída, DB no
# disponible momentáneamente, deadlock). Errores de tipo / constraint
# violations NO se reintentan: el INSERT volvería a fallar igual.
_RETRYABLE_PG_EXC: tuple[type[BaseException], ...] = (
    psycopg.OperationalError,
    psycopg.errors.DeadlockDetected,
    psycopg.errors.SerializationFailure,
)


class PostgresWriter:
    """Writer thread-safe de resultados de scraping hacia PostgreSQL.

    Usa un connection pool interno (psycopg_pool.ConnectionPool) con
    min_size=1 / max_size=4 — suficiente para el scraper que corre
    secuencialmente los productos. Para paralelizar (parallelism del Job)
    subir max_size al número de workers concurrentes.

    El pool se inicializa lazy en el primer `insert_results()` para no
    abrir conexiones durante el import del módulo (importante en tests).

    Attributes:
        dsn: Cadena de conexión Postgres (postgresql://user:pass@host:port/db).
        min_size: Tamaño mínimo del pool (conexiones siempre abiertas).
        max_size: Tamaño máximo del pool (conexiones bajo demanda).
    """

    def __init__(
        self,
        dsn: str,
        min_size: int = 1,
        max_size: int = 4,
    ) -> None:
        """Inicializa el writer sin abrir conexiones todavía.

        Args:
            dsn: DSN de Postgres. Ejemplo:
                ``postgresql://scraper:changeme-en-prod@postgres:5432/scraper``.
            min_size: Conexiones que el pool mantiene abiertas siempre.
            max_size: Tope de conexiones simultáneas que el pool abrirá.

        Raises:
            ValueError: Si el DSN está vacío.
        """
        if not dsn:
            raise ValueError("dsn no puede estar vacío")
        self.dsn: str = dsn
        self.min_size: int = min_size
        self.max_size: int = max_size
        self._pool: ConnectionPool | None = None

    def _ensure_pool(self) -> ConnectionPool:
        """Inicializa el pool al primer uso (lazy)."""
        if self._pool is None:
            logger.info(
                "Inicializando connection pool (min=%d, max=%d)",
                self.min_size,
                self.max_size,
            )
            self._pool = ConnectionPool(
                conninfo=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                # open=True hace que el pool levante las conexiones mínimas
                # ya en el constructor y falle rápido si la DB no responde.
                open=True,
                # Timeout de conexión razonable para entorno k8s donde el
                # Service puede tardar unos segundos en estar Ready.
                timeout=10.0,
            )
        return self._pool

    @with_backoff(max_attempts=3, base_delay=2.0, exceptions=_RETRYABLE_PG_EXC)
    def insert_results(
        self,
        producto: str,
        items: Iterable[dict[str, Any]],
    ) -> int:
        """Inserta los resultados de un scrape en `scrape_results`.

        Toda la operación corre en una transacción única: o se insertan todos
        los items o ninguno. `scraped_at` se llena con `NOW()` de la base.

        Args:
            producto: Nombre del producto buscado (ej: "Bicicleta rodado 29").
                Va a la columna ``producto`` de cada fila.
            items: Iterable de dicts con los campos extraídos. Las claves
                aceptadas son las definidas en ``_ITEM_COLUMNS``. Otras se
                ignoran. Faltantes se insertan como NULL.

        Returns:
            Cantidad de filas insertadas (igual a len(items) si todo OK).

        Raises:
            ValueError: Si ``producto`` está vacío.
            psycopg.Error: Si tras 3 intentos sigue fallando una excepción
                no transitoria (constraint violation, type error, etc.).
        """
        if not producto:
            raise ValueError("producto no puede estar vacío")

        items_list = list(items)
        if not items_list:
            logger.info("Sin items que insertar para producto=%r — skip", producto)
            return 0

        # Statement parametrizado. Construimos las columnas y placeholders
        # dinámicamente para que cualquier cambio en _ITEM_COLUMNS se refleje.
        cols_sql = ", ".join(("producto", *_ITEM_COLUMNS))
        placeholders = ", ".join(["%s"] * (1 + len(_ITEM_COLUMNS)))
        stmt = f"INSERT INTO scrape_results ({cols_sql}) VALUES ({placeholders})"

        rows = [(producto, *(item.get(col) for col in _ITEM_COLUMNS)) for item in items_list]

        pool = self._ensure_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # executemany en psycopg3 es eficiente para batches chicos
                # (≤ 100 filas). Para batches grandes usar cur.copy() o
                # `psycopg.extras.execute_values` (psycopg2). El scraper del
                # TP devuelve ~10 items por producto, así que executemany
                # alcanza y sobra.
                cur.executemany(stmt, rows)
                inserted = cur.rowcount
            # __exit__ del `with conn` hace commit si no hubo excepción.
        logger.info(
            "Insertados %d resultados en scrape_results para producto=%r",
            inserted,
            producto,
        )
        return inserted

    def fetch_latest(
        self,
        producto: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Devuelve los últimos N resultados de un producto (helper de debug).

        Útil para verificar desde un test o desde un REPL que las inserciones
        están aterrizando bien. NO está pensado para servir queries en hot path.

        Args:
            producto: Producto a consultar.
            limit: Cantidad máxima de filas a devolver.

        Returns:
            Lista de dicts (una por fila) ordenados por scraped_at desc.
        """
        pool = self._ensure_pool()
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, producto, titulo, precio, link, tienda_oficial,
                           envio_gratis, cuotas_sin_interes, scraped_at
                    FROM scrape_results
                    WHERE producto = %s
                    ORDER BY scraped_at DESC
                    LIMIT %s
                    """,
                    (producto, limit),
                )
                return list(cur.fetchall())

    def close(self) -> None:
        """Cierra el pool. Llamar al apagar el scraper."""
        if self._pool is not None:
            logger.info("Cerrando connection pool")
            self._pool.close()
            self._pool = None

    def __enter__(self) -> PostgresWriter:
        self._ensure_pool()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
