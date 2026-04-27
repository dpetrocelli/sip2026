# LogQL Cheatsheet — TP 3 ML Scraper

Diez queries LogQL útiles para investigar el comportamiento del scraper desde Grafana → Explore → Loki, o desde la API HTTP de Loki directo.

Convención usada en estos ejemplos:

- El selector base es `{namespace="ml-scraper"}` (todos los pods del scraper).
- `|=` filtra líneas que **contienen** un string literal.
- `!=` filtra líneas que **no** contienen ese string.
- `| json` parsea la línea como JSON y expone sus campos como labels temporarios para esa pipeline.
- Rangos: `[5m]`, `[1h]`, `[24h]` — todos relativos al tiempo de la query.

---

### 1. Conteo total de logs en las últimas 24h

**Intención:** sanity check inicial. ¿Está llegando algo a Loki? ¿Cuánto volumen genera el scraper?

```logql
sum(count_over_time({namespace="ml-scraper"} [24h]))
```

**Output esperado:** un número, ej `1247`. Si da `0` algo está mal en Alloy o en el discovery del namespace.

---

### 2. Filtrar logs por producto

**Intención:** ver solo los logs relacionados con un producto puntual (ej. iPhone). El label `producto` se promueve desde el JSON del scraper si usa el formato sugerido en `scraper-json-logging.py`.

```logql
{namespace="ml-scraper", producto="iPhone 16 Pro Max"}
```

**Output esperado:** stream de logs solo de esa búsqueda. Si el label no se promovió usar el fallback con `|=`:

```logql
{namespace="ml-scraper"} |= "iPhone 16 Pro Max"
```

---

### 3. Filtrar logs por nivel (solo errores)

**Intención:** dejar de ver el ruido INFO/DEBUG y mirar solo lo que falló.

```logql
{namespace="ml-scraper", level="ERROR"}
```

**Output esperado:** todas las líneas con `"level": "ERROR"`. Si se quiere incluir CRITICAL también:

```logql
{namespace="ml-scraper"} | json | level=~"ERROR|CRITICAL"
```

---

### 4. Tasa de errores por minuto (últimos 30 min)

**Intención:** ¿el ritmo de errores está subiendo? Útil para alertas y dashboards.

```logql
sum(rate({namespace="ml-scraper", level="ERROR"} [1m]))
```

**Output esperado:** un timeseries en errores/seg. Multiplicar por 60 para errores/min mental. Si pasa de 0.05 (3 errores/min) durante 5+ min, pasa algo serio.

---

### 5. Latencia entre primer y último log por Job (unwrap + duration_seconds)

**Intención:** medir cuánto tarda cada corrida del scraper. Requiere que el scraper emita `extra={"duration_seconds": <float>}` al loggear el resumen final.

```logql
quantile_over_time(0.95,
  {namespace="ml-scraper", event="job_finished"}
  | json
  | unwrap duration_seconds
  [1h]
) by (pod)
```

**Output esperado:** P95 de duración por pod, en segundos. Si sube de golpe sospechar de mercadolibre.com lento o de selectores rotos.

---

### 6. Últimos N errores con contexto

**Intención:** "¿qué fue lo último que falló?". Limita el output para no traer 10k líneas.

```logql
{namespace="ml-scraper", level="ERROR"} | json | line_format "{{.timestamp}} [{{.producto}}] {{.message}}"
```

**Output esperado:** líneas formateadas tipo `2026-04-26T15:42:01 [iPhone 16 Pro Max] Timeout esperando filtros`. Para limitar a las últimas 20: usar el límite del panel de Grafana o `?limit=20` en la API.

---

### 7. Top productos por scrapes exitosos

**Intención:** ranking — qué producto se completó más veces. Detecta sesgos (ej. uno siempre falla y baja el ranking).

```logql
topk(5,
  sum by (producto) (
    count_over_time({namespace="ml-scraper"} |= "JSON escrito" [24h])
  )
)
```

**Output esperado:** los 5 productos con más éxitos en 24h. Si la corrida emite siempre los mismos 3 productos esperamos `3` líneas con el conteo de corridas.

---

### 8. Por qué falló — buscar tracebacks/excepciones

**Intención:** capturar el contexto completo de las excepciones, no solo la línea ERROR. Las stacktraces vienen en líneas multilinea o con `Traceback (most recent call last):`.

```logql
{namespace="ml-scraper"}
  |~ "Traceback|Exception|Error:"
  != "ErrorBoundary"
```

**Output esperado:** todas las líneas que matchean traceback o nombre de excepción, excluyendo el ruido de "ErrorBoundary" si aparece. El operador `|~` es regex (case-sensitive por default).

---

### 9. Comparar hoy vs ayer (rangos paralelos)

**Intención:** ¿hoy estamos peor que ayer? Útil para detectar regresiones después de un deploy.

```logql
# Errores de las últimas 6h:
sum(count_over_time({namespace="ml-scraper", level="ERROR"} [6h]))

# Y por separado, los errores de hace 24h-30h (mismas 6h pero del día anterior):
sum(count_over_time({namespace="ml-scraper", level="ERROR"} [6h] offset 24h))
```

**Output esperado:** dos números. Si el primero es mucho mayor que el segundo, hoy está peor. En Grafana se pueden poner los dos como series separadas en el mismo panel para ver la comparación visualmente.

---

### 10. Productos distintos vistos en una corrida

**Intención:** "¿cuántos productos distintos arrancó el scraper en su última corrida?". Útil para validar que el `--products` parametrizado se respetó.

```logql
count(
  count by (producto) (
    {namespace="ml-scraper"} |= "=== Producto" [10m]
  )
)
```

**Output esperado:** un número entero, ej `3` para la corrida default. Si da `1` el scraper se quedó pegado en el primer producto, si da `0` no arrancó.

---

## Sintaxis avanzada — apéndice rápido

| Operador | Significado | Ejemplo |
|----------|-------------|---------|
| `=` | label match exacto | `{namespace="ml-scraper"}` |
| `!=` | label no match | `{namespace!="kube-system"}` |
| `=~` | label match regex | `{level=~"ERROR\|WARN"}` |
| `!~` | label no match regex | `{pod!~"loki-.*"}` |
| `\|=` | line filter contains | `\|= "JSON escrito"` |
| `!=` | line filter not contains | `!= "DEBUG"` |
| `\|~` | line filter regex | `\|~ "Timeout\|Connection"` |
| `\| json` | parsea cuerpo como JSON | `\| json` |
| `\| logfmt` | parsea cuerpo como key=val | `\| logfmt` |
| `\| unwrap X` | promueve X a métrica | `\| unwrap duration_seconds` |
| `rate(...)` | eventos/segundo | `rate({app="x"} [5m])` |
| `count_over_time(...)` | total en el rango | `count_over_time({...} [1h])` |
| `sum by (label) (...)` | agrega manteniendo label | `sum by (producto) (count_over_time(...))` |

## Cómo correr una query desde la línea de comandos

Sin abrir Grafana, contra el Service interno de Loki:

```bash
# Port-forward a Loki:
kubectl port-forward -n observability svc/loki 3100:3100

# Query instant:
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query=sum(count_over_time({namespace="ml-scraper"} [24h]))' \
  | jq .

# Query range (con timestamps):
curl -G -s 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={namespace="ml-scraper", level="ERROR"}' \
  --data-urlencode 'start='"$(date -u -d '1 hour ago' +%s)000000000" \
  --data-urlencode 'end='"$(date -u +%s)000000000" \
  --data-urlencode 'limit=100' \
  | jq '.data.result[].values[]'
```

## Referencias

- LogQL spec oficial: <https://grafana.com/docs/loki/latest/query/>
- Cheatsheet de Grafana: <https://grafana.com/docs/loki/latest/query/log_queries/>
- API HTTP de Loki: <https://grafana.com/docs/loki/latest/reference/loki-http-api/>
