# Hit #5 — Robustez, retries y logging estructurado

Endurecimiento del Hit #4 con cuatro mejoras clave:

1. **Selectores centralizados** en [`ml_selectors.py`](ml_selectors.py). Un cambio de DOM en MercadoLibre se arregla en un único lugar.
2. **Retries con backoff exponencial** en [`retry.py`](retry.py): decorador `@with_backoff(max_attempts=3, base_delay=2.0)` que reintenta ante `TimeoutException`, `StaleElementReferenceException` y `WebDriverException` con espera 2s/4s/8s.
3. **Aislamiento por producto**: si un producto falla después de 3 intentos, se loguea y se continúa con los siguientes — nunca rompe la corrida entera.
4. **Logging estructurado** a archivo (`logs/scraper.log` con rotación) y stdout simultáneamente, con nivel y nombre del módulo.

## Estructura del módulo

```
hit5/
├── README.md           ← este archivo
├── main.py             ← entrypoint con logging + retries aplicados
├── browser_factory.py  ← copia del Hit #2 (factory chrome/firefox)
├── filters.py          ← copia del Hit #3 (cookies + filtros DOM)
├── extractors.py       ← copia del Hit #4 (6 campos, soft-fail a null)
├── ml_selectors.py        ← NUEVO — todos los selectores en un solo módulo
└── retry.py            ← NUEVO — decorador @with_backoff
```

## Cómo correr

```bash
# Los 3 productos en Chrome headless
HEADLESS=true BROWSER=chrome python hit5/main.py

# Con producto custom y browser explícito
python hit5/main.py --browser firefox --products "GeForce RTX 5090"

# Con límite custom
python hit5/main.py --limit 20
```

## Output

- `output/<slug>.json` — array de hasta N resultados con el schema del Hit #4.
- `logs/scraper.log` — log rotado (2 MB, 3 archivos de backup) con todos los reintentos y errores.

Ejemplo de log con retry disparado:

```
2026-04-26 16:42:11,003 [INFO] __main__ — === Producto: 'iPhone 16 Pro Max' ===
2026-04-26 16:42:13,210 [WARNING] retry — search_and_filter intento 1/3 falló (TimeoutException), reintentando en 2.0s
2026-04-26 16:42:25,440 [INFO] filters — Filtros aplicados: ['nuevo', 'tienda_oficial']
2026-04-26 16:42:25,441 [INFO] __main__ — 'iPhone 16 Pro Max' → 10 resultados
2026-04-26 16:42:25,452 [INFO] __main__ — JSON escrito: output/iphone_16_pro_max.json (10 registros)
```

## Decisiones de diseño

- **`@with_backoff` aplicado solo a `search_and_filter`** y no a `collect_results` — los retries tienen sentido cuando hay una operación de red costosa que puede fallar transitoriamente (load de página, navegación). Re-extraer del DOM ya cargado no se beneficia de esperas.
- **Excepción genérica en `collect_results`** captura errores por card (`extract_result` puede tirar cualquier cosa si una card está mal armada) y degrada esa card a `null`/skip — no rompe el resto.
- **Logging via `logging.handlers.RotatingFileHandler`** evita que el archivo crezca infinito si el scraper corre como CronJob (Hit #8).
