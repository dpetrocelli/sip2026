# Hit #3 — Filtros DOM + Screenshot

## Qué agrega respecto al Hit #2

- Módulo `filters.py` con `apply_all_filters(driver)` que aplica tres filtros
  vía clicks reales sobre el DOM (no modificación de URL):
  - **Condición = Nuevo**
  - **Tienda Oficial = Sí**
  - **Ordenar = Más relevantes**
- Manejo del banner de cookies que bloquea los filtros en ML.
- Captura de screenshot a `screenshots/<producto>_<browser>.png` después
  de aplicar los filtros.
- `browser_factory.py` copiado del Hit #2 (misma lógica, mismo comportamiento).

## Cómo ejecutar

```bash
# Chrome (default), producto default "bicicleta rodado 29"
python hit3/main.py

# Firefox via env var
BROWSER=firefox python hit3/main.py

# Producto custom
python hit3/main.py --product "iPhone 16 Pro Max"

# Headless + Firefox
HEADLESS=true BROWSER=firefox python hit3/main.py --product "GeForce RTX 5090"
```

## Estructura

```
hit3/
├── README.md
├── browser_factory.py   ← copia del Hit #2 (sin cambios)
├── filters.py           ← clicks DOM: Nuevo, Tienda Oficial, Más relevantes
└── main.py              ← orchestration: buscar → filtrar → screenshot → imprimir
```

## Output esperado

```
[INFO] Iniciando browser: chrome (headless=False)
[INFO] Navegando a https://www.mercadolibre.com.ar
[INFO] Búsqueda: 'bicicleta rodado 29'
[INFO] Esperando resultados...
[INFO] Banner de cookies cerrado
[INFO] Filtro 'Nuevo' aplicado
[INFO] Filtro 'Tienda Oficial' aplicado
[INFO] Ordenamiento 'Más relevantes' aplicado
[INFO] Estado de filtros: {'nuevo': True, 'tienda_oficial': True, 'mas_relevantes': True}
[INFO] URL final: https://www.mercadolibre.com.ar/...
[INFO] Screenshot guardado en: screenshots/bicicleta_rodado_29_chrome.png
1. Bicicleta Mountain Bike Rodado 29 ...
2. ...
```

El screenshot se guarda en:

```
screenshots/
├── bicicleta_rodado_29_chrome.png
└── bicicleta_rodado_29_firefox.png
```

La imagen muestra el panel lateral con los filtros activos ("Nuevo" y "Tienda oficial" tildados).

## Decisiones de diseño

- **Cada filtro es idempotente e independiente**: si un filtro no está
  disponible para el producto buscado (ej: RTX 5090 sin tiendas oficiales),
  se loguea una advertencia y se continúa sin romper el flujo. La función
  retorna un `dict[str, bool]` con el estado de cada filtro.
- **Banner de cookies antes de filtros**: ML superpone el banner sobre los
  links de filtro. Se intenta cerrarlo con 6 selectores alternativos (el DOM
  de ML varía entre deploys). Si no aparece, se continúa silenciosamente.
- **`_safe_click`**: ante `ElementClickInterceptedException` (banner residual
  u overlay), se hace fallback a JS click. No es el path feliz, pero se
  documenta en el log para visibilidad.
- **XPath con `normalize-space`**: los spans de ML tienen whitespace
  irregular. `normalize-space(text())='Nuevo'` es más robusto que match
  exacto sobre el texto raw.
- **`sys.path.insert` para browser_factory**: el Hit #3 importa su propia
  copia de `browser_factory.py` (en el mismo directorio) para que cada hit
  sea auto-contenido y ejecutable desde la raíz del repo con
  `python hit3/main.py`.
