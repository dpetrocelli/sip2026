# Hit #4 — Extracción estructurada a JSON

Extiende el Hit #3 para iterar **los 3 productos** del enunciado y extraer 10 resultados con campos estructurados a JSON.

## Productos objetivo

1. `bicicleta rodado 29`
2. `iPhone 16 Pro Max`
3. `GeForce RTX 5090`

## Schema del JSON de salida

Cada archivo `output/<slug_producto>.json` es un array de objetos:

```json
[
  {
    "titulo": "Bicicleta Mountain Bike Rodado 29...",
    "precio": 350000.0,
    "link": "https://articulo.mercadolibre.com.ar/...",
    "tienda_oficial": "BikeStore",
    "envio_gratis": true,
    "cuotas_sin_interes": "12x $29.166 sin interés"
  }
]
```

Tipos:

| Campo | Tipo | Faltante |
|-------|------|----------|
| `titulo` | str | — |
| `precio` | float (ARS, sin separadores) | `null` |
| `link` | str (URL absoluta) | `null` |
| `tienda_oficial` | str | `null` |
| `envio_gratis` | bool | `false` |
| `cuotas_sin_interes` | str | `null` |

## Cómo correr

```bash
# Los 3 productos en Chrome headless
HEADLESS=true BROWSER=chrome python hit4/main.py

# Solo un producto, en Firefox
python hit4/main.py --browser firefox --products "iPhone 16 Pro Max"

# Con límite custom
python hit4/main.py --limit 5
```

## Output esperado

- `output/bicicleta_rodado_29.json` — 10 objetos
- `output/iphone_16_pro_max.json` — 10 objetos
- `output/geforce_5090.json` — 10 objetos

## Diseño

- Cada extractor en `extractors.py` falla soft a `null` si el campo no está en el DOM (no rompe la card entera).
- Los 3 productos se procesan secuencialmente con UN solo browser (no spawneamos un driver por producto — costo alto y poco beneficio).
- El campo `precio` se limpia con regex `[^\d]` para sacar `$`, puntos y espacios y convertir a `float`.
- Si todo el scraping de un producto falla (timeout fatal), el JSON se escribe igual con array vacío para que el resto de la corrida continúe.
