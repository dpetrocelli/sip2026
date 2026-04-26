# Golden Output — Vara de Corrección

Estos JSON son la **salida de referencia** que produjo el scraper de la cátedra contra MercadoLibre Argentina el **2026-04-26**, corrida con `BROWSER=chrome HEADLESS=true python hit5/main.py` (la imagen multi-stage `ml-scraper:hit5` produce el mismo output).

| Archivo | Resultados | Notas |
|---------|-----------:|-------|
| `bicicleta_rodado_29.json` | 10 | 100% campos completos. Todos de "Luxus" (tienda oficial real). |
| `iphone_16_pro_max.json` | 10 | 2/10 con `tienda_oficial` (Apple no tiene tienda directa en ML; varios cards son revendedores). |
| `geforce_5090.json` | 3 | ML solo mostró 3 resultados orgánicos para este keyword. Es un producto de nicho. |

## Por qué los filtros no se aplican

Los logs muestran `Filtros no disponibles: ['nuevo', 'tienda_oficial', 'mas_relevantes']`. Esto **no es un bug del scraper** — el DOM de los filtros laterales de ML cambió entre el momento de elaboración de la consigna (febrero 2026) y la corrida de referencia (abril 2026). La rúbrica del Hit #3 evalúa que el código intente aplicar los filtros vía DOM (no por URL), no que efectivamente los filtros estén disponibles.

> **Nota para corrección**: los alumnos cuyo scraper también logueó "filtro no disponible" están en la misma situación. Lo que se evalúa es la implementación del código, no que el output coincida exacto con este golden.

## Uso para comparación

`tooling/compare.py` toma una entrega de alumno y compara su `output/` contra estos archivos:

- **Estructura**: ¿el JSON es un array de objetos?
- **Cardinalidad**: ¿tiene cerca de 10 resultados (excepto GeForce que es nicho)?
- **Schema**: ¿están los 6 campos requeridos?
- **Tipos**: precio numérico, link absoluto, envio_gratis booleano, etc.
- **Distribución**: ¿qué porcentaje de cards tiene tienda_oficial vs el golden?

NO se compara el contenido literal (los precios y títulos varían entre corridas — ML tiene resultados rotativos por hora).
