# Corrección TP2 — Parte 2: Logging centralizado con EFK (Elasticsearch + Fluent Bit + Kibana)

**Grupo:** Proxy Team
**Integrantes:**
- Ponti, Mateo Daniel
- Scialchi, Luciano Agustin
- Romero Monteagudo, Valentín Joel
- Cacciatore, Bautista
- Correa, Miqueas
**Repo GitHub:** https://github.com/correamiq/Testing-Selenium-ProxyTeam
**Video (YouTube):** _______________________________________________
**Fecha de entrega:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) — Loki sigue corriendo en `observability` | ✅ OK | P1: 8.1/10 |
| B2 | Existe `efk/install.sh` ejecutable (carpeta separada de `observability/`) | ✅ OK | 5.2 KB, `set -e` |
| B3 | `install.sh` levanta el stack completo desde cero en cluster limpio | ✅ OK | Verifica estado con `kubectl wait` |
| B4 | Versiones pinneadas: ECK `2.16.x`, ES/Kibana `8.17.x`, Fluent Bit `3.2.x` — NO `latest` | ✅ OK | ECK 2.16.0, ES/Kibana 8.17.3, FB 3.2.4 |
| B5 | NO usa Fluentd (usa Fluent Bit) — si usa Fluentd: -5 % automático | ✅ OK | Fluent Bit DaemonSet ✓ |
| B6 | NO usa chart deprecado `elastic/elasticsearch` — sólo ECK Operator | ✅ OK | ECK CRD `elasticsearch.k8s.elastic.co/v1` ✓ |
| B7 | `gitleaks detect` da 0 leaks (sin password elastic ni webhook Discord en repo) | ✅ OK | Password obtenida via `kubectl get secret` ✓ |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | CI + checklist en README ✓ |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

**Penalizaciones automáticas:**

| Penalización | Descuento | Aplica |
|---|---|---|
| Usa Fluentd en lugar de Fluent Bit | -5 pts | ☐ |
| Parte 1 rota / Loki no corre al momento de evaluar | -10 pts | ☐ |

---

## HIT #1 — ECK Operator + Elasticsearch + Kibana (20 puntos)

### 1.1 Estructura del repositorio (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe carpeta `efk/` con `README.md` (separada de `observability/`) | 1 | 1 | ✓ |
| Existen `helm/eck-operator-values.yaml` y `helm/fluent-bit-values.yaml` | 1 | 1 | ✓ |
| Existen `manifests/namespace.yaml`, `elasticsearch.yaml`, `kibana.yaml`, `kibana-nodeport.yaml`, `ilm-policy.json` | 1 | 1 | ✓ |
| Existe `efk/install.sh` idempotente con todos los pasos | 1 | 1 | ✓ |

**Subtotal 1.1:** 4 / 4

### 1.2 ECK Operator y CRDs (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| ECK Operator instalado via chart `elastic/eck-operator` versión `2.16.x` | 2 | 2 | 2.16.0 ✓ |
| CR `Elasticsearch` definido via CRD `elasticsearch.k8s.elastic.co/v1` (no chart legacy) | 2 | 2 | ✓ |
| Resources ECK Operator dentro de límites (≤ 100m CPU, ≤ 256Mi RAM) | 1 | 1 | ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Elasticsearch (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Version `8.17.x` declarada en el CR | 1 | 1 | 8.17.3 ✓ |
| `number_of_replicas: 0` en el index template (evita estado `yellow` en single-node) | 2 | 2 | ✓ |
| Resources dentro de límites: requests ≤ 1Gi RAM / limits ≤ 2Gi RAM; PVC 10Gi `local-path` | 2 | 2 | ✓ |

**Subtotal 1.3:** 5 / 5

### 1.4 Kibana (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CR `Kibana` definido via CRD, versión `8.17.x` | 1 | 1 | 8.17.3 ✓ |
| Service NodePort 30001 funcional | 1 | 1 | ✓ |
| Resources dentro de límites (≤ 500m CPU, ≤ 1Gi RAM) | 1 | 1 | ✓ |
| Password del usuario `elastic` gestionada por ECK (no commiteada) | 1 | 1 | `kubectl get secret` en install.sh ✓ |

**Subtotal 1.4:** 4 / 4

### 1.5 Verificación de funcionamiento (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Elasticsearch status = `green` tras `install.sh` (evidencia en video) | 1 | 1 | ✓ |
| Kibana status = `available` y accesible en :30001 (evidencia en video) | 1 | 1 | ✓ |

**Subtotal 1.5:** 2 / 2

### Observaciones Hit #1
```
Stack ECK completo y bien configurado. Versiones correctas, CRDs bien usados,
number_of_replicas: 0 para single-node. Sin observaciones negativas.
```

**TOTAL HIT #1:** 20 / 20

---

## HIT #2 — Fluent Bit como DaemonSet, pipeline al scraper (20 puntos)

### 2.1 Instalación y configuración base (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Chart `fluent/fluent-bit` versión `0.48.x`, imagen tag `3.2.x` (no `latest`) | 2 | 2 | chart 0.48.x, imagen 3.2.4 ✓ |
| DaemonSet running con `tolerations` para nodo control-plane k3s (single-node) | 1 | 1 | ✓ |
| RBAC configurado (`serviceAccount.create: true`, `rbac.create: true`) | 1 | 1 | ✓ |
| Resources dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 0 | Resources declarados en exactamente los límites (64Mi/128Mi). Dentro de rango pero sin headroom. |

**Subtotal 2.1:** 4 / 5

### 2.2 Pipeline Input → Parser → Filter → Output (10 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Input `kubernetes` configurado leyendo de `/var/log/containers/` | 2 | 2 | ✓ |
| Parser JSON correcto (parsea el JSON del scraper emitido por `logging_setup.py`) | 3 | 3 | ✓ |
| Filter `Kubernetes` para enriquecer con metadata (namespace, pod, labels) | 2 | 2 | ✓ |
| Output Elasticsearch apuntando al cluster ECK con TLS (cert montado via extraVolumes) | 3 | 3 | Cert de ECK montado correctamente ✓ |

**Subtotal 2.2:** 10 / 10

### 2.3 Evidencia de indexado (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Índices `scraper-logs-*` aparecen en Elasticsearch (evidencia en video/Kibana) | 3 | 3 | ✓ |
| Campos JSON del scraper visibles como fields en Kibana Discover (no como string crudo) | 2 | 2 | ✓ |

**Subtotal 2.3:** 5 / 5

### Observaciones Hit #2
```
Pipeline bien configurado end-to-end. El único detalle: resources de Fluent Bit
declarados en exactamente los límites (requests = limits = 64Mi/128Mi), sin margen.
No es bloqueante, pero con OOM en el futuro el pod se reinicia sin warning previo.
```

**TOTAL HIT #2:** 19 / 20

---

## HIT #3 — Index pattern + ILM (rollover, retention 7 días) (15 puntos)

### 3.1 ILM policy (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/manifests/ilm-policy.json` commiteado | 1 | 1 | ✓ |
| Policy tiene 3 fases: `hot` → `warm` → `delete` | 2 | 2 | ✓ |
| Fase `hot`: rollover por `max_age: 1d` o `max_primary_shard_size: 1gb` | 2 | 2 | max_age: 1d ✓ |
| Fase `delete`: `min_age: 7d` (retención total = 7 días, equivalente a Parte 1) | 2 | 2 | ✓ |

**Subtotal 3.1:** 7 / 7

### 3.2 Index template asociado (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Index template `scraper-logs-template` aplicado a patrón `scraper-logs-*` | 2 | 2 | ✓ |
| `number_of_shards: 1`, `number_of_replicas: 0` configurados (evita `yellow`) | 2 | 2 | ✓ |

**Subtotal 3.2:** 4 / 4

### 3.3 Data view en Kibana + evidencia (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Data view `scraper-logs` con index pattern `scraper-logs-*` y timestamp `@timestamp` creado | 2 | 2 | ✓ |
| Policy `scraper-logs` visible en Kibana → Stack Management → Index Lifecycle Policies (evidencia) | 1 | 1 | ✓ |
| Policy aplicada en `install.sh` via API curl (no manual en UI) | 1 | 1 | `curl -s -XPUT` con header `kbn-xsrf: true` ✓ |

**Subtotal 3.3:** 4 / 4

### Observaciones Hit #3
```
ILM policy completa y bien implementada. Las 3 fases correctas. install.sh aplica
todo via curl con header kbn-xsrf correcto. Sin observaciones.
```

**TOTAL HIT #3:** 15 / 15

---

## HIT #4 — Cookbook KQL: 6+ queries útiles (15 puntos)

### 4.1 Archivo y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/queries/kql-cookbook.md` | 1 | 1 | ✓ |
| Usa KQL exclusivamente (no `language: lucene`) | 1 | 1 | ✓ |
| Cada query documenta: pregunta · KQL · equivalente Lucene · por qué | 1 | 1 | ✓ |

**Subtotal 4.1:** 3 / 3

### 4.2 Queries obligatorias (10 pts)

| Query | Presente | KQL correcto | Funciona | Pts |
|-------|----------|-------------|----------|-----|
| Q1 — Errores por producto últimas 24h (`level: "ERROR" and producto: *`) | ✅ | ✅ | ✅ | 2 |
| Q2 — Top selectores faltantes (`message: "Filtro * no disponible"`) | ✅ | ✅ | ✅ | 2 |
| Q3 — Distribución duración del Job (`event: "scrape_completado"`) | ✅ | ✅ | ✅ | 2 |
| Q4 — Timeouts de Selenium (`message: *timeout*`) | ✅ | ✅ | ✅ | 1 |
| Q5 — Eventos de CronJob específico por `kubernetes.labels.job_name` | ✅ | ✅ | ✅ | 1 |
| Q6 — Errores excluyendo módulo Postgres (`level: "ERROR" and not logger: "psycopg*"`) | ✅ | ✅ | ✅ | 2 |

**Subtotal 4.2:** 10 / 10

### 4.3 Comparativa KQL vs LogQL (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El cookbook menciona explícitamente diferencias con las queries de Parte 1 (KQL vs LogQL) | 2 | 1 | Hay una mención superficial al final del cookbook pero no hay comparación side-by-side ni análisis de por qué la sintaxis difiere. −1 pt. |

**Subtotal 4.3:** 1 / 2

### Observaciones Hit #4
```
Las 6 queries requeridas están presentes con KQL correcto y equivalente Lucene. La
comparativa KQL vs LogQL es escueta — menciona que "KQL es más intuitivo para queries
estructuradas" pero no contrasta las mismas queries de ambos cookbooks. Para la defensa:
preparar un ejemplo concreto de Q1 en LogQL vs KQL mostrando la diferencia de sintaxis.
```

**TOTAL HIT #4:** 14 / 15

---

## HIT #5 — Dashboard Kibana provisionado as-code (NDJSON + import API) (20 puntos)

> **ATENCIÓN:** `efk/dashboards/scraper-overview.ndjson` es un archivo de texto plano con el contenido literal "reemplazar con el export real de Kibana". No es un NDJSON exportado. `efk/dashboards/export.ndjson` (726 bytes) es sólo un index-pattern export, no un dashboard completo.

### 5.1 Provisioning as-code (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/dashboards/scraper-overview.ndjson` commiteado | 2 | 2 | Archivo existe (727 bytes) pero es un placeholder textual. |
| NDJSON exportado con "Include related objects" (data view + visualizaciones incluidas) | 2 | 0 | Placeholder — no es un export real de Kibana |
| `install.sh` importa el NDJSON via `POST /api/saved_objects/_import` con header `kbn-xsrf: true` | 3 | 0 | install.sh no llama a la Saved Objects API |
| Password de elastic obtenida por `kubectl get secret` (no hardcodeada en el script) | 1 | 1 | ✓ (para otros calls del script) |

**Subtotal 5.1:** 3 / 8

### 5.2 Contenido del dashboard — mínimo 6 paneles (8 pts)

| Panel | Presente | Datos reales | Pts |
|-------|----------|-------------|-----|
| Metric — Total de eventos hoy | ☐ | ☐ | 0 |
| Metric — % eventos `level: "ERROR"` vs total | ☐ | ☐ | 0 |
| Bar chart — Top 5 productos con más errores | ☐ | ☐ | 0 |
| Pie chart — Distribución por `level` (INFO / WARNING / ERROR) | ☐ | ☐ | 0 |
| Line chart — Eventos por minuto last 6h, breakdown por `level` | ☐ | ☐ | 0 |
| Table — Última corrida exitosa por producto | ☐ | ☐ | 0 |

**Subtotal 5.2:** 0 / 8

### 5.3 Calidad del NDJSON (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| NDJSON parseable sin errores (no JSON roto) | 1 | 0 | No es NDJSON, es texto plano |
| Import retorna `"success": true` (evidencia en video o log) | 2 | 0 | No se importa |
| Dashboard visible en Kibana → Dashboards con datos reales (no "No results found") | 1 | 0 | No se importa |

**Subtotal 5.3:** 0 / 4

### Observaciones Hit #5
```
El archivo scraper-overview.ndjson contiene "reemplazar con el export real de Kibana"
— es un placeholder explícito. export.ndjson (726 bytes) es solo el index-pattern,
no el dashboard completo. install.sh no invoca la Saved Objects API para importar.

Para remediar: en Kibana → Dashboards → crear el dashboard con los 6 paneles,
luego Saved Objects → Export con "Include related objects" habilitado.
Guardar el resultado como scraper-overview.ndjson y agregar en install.sh:
  curl -X POST "http://localhost:30001/api/saved_objects/_import" \
    -H "kbn-xsrf: true" \
    -F file=@efk/dashboards/scraper-overview.ndjson
```

**TOTAL HIT #5:** 3 / 20

---

## ADR — `0009-stack-de-logging-efk.md` (10 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0009-stack-de-logging-efk.md` (numeración continua) | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| Extensión adecuada (no genérico ni copiado de la consigna) | 1 | 1 | ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Compara footprint real medido en el cluster (Loki ≈ 256Mi vs ES ≈ 2Gi) | 2 | 2 | Cifras propias del cluster ✓ |
| Compara latencia de query (full-text search de ES vs label-first de Loki) | 2 | 2 | ✓ |
| Menciona licencia Elastic License v2 (ELv2) y que NO es OSS-OSI + alternativa OpenSearch | 2 | 1 | ELv2 mencionada y non-OSI explicado. Pero OpenSearch como fork/alternativa no aparece explícitamente — solo dice "existen alternativas OSS" sin nombrar OpenSearch. |
| Conclusión abierta — no sentencia cuál es mejor, remite a Parte 4 para el ADR comparativo | 1 | 1 | ✓ |

**Subtotal 6.2:** 6 / 7

### Observaciones ADR
```
ADR 0009 sólido. Compara footprint y latencia con datos propios. ELv2 bien explicada.
Lo que falta: nombrar OpenSearch explícitamente como el fork creado por AWS en respuesta
a ELv2 (2021) — es el ejemplo concreto que demuestra que el riesgo de licencia ya se
materializó en la comunidad. Una línea alcanza: "AWS forkeó Elasticsearch y Kibana
como OpenSearch/OpenSearch Dashboards en 2021 al cambio de licencia."
```

**TOTAL ADR:** 9 / 10

---

## BONUS — Hit #6: Alertas via Kibana Alerting (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Connector Discord configurado via Webhook (URL por env var, no commiteada) | 1 | 0 | No implementado |
| Rule type "Elasticsearch query" con KQL `level: "ERROR"`, threshold > 5, window 1h | 2 | 0 | No implementado |
| Screenshot o evidencia de notificación recibida en Discord | 2 | 0 | No implementado |

**TOTAL BONUS Hit #6:** 0 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 2

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — ECK + Elasticsearch (green) + Kibana | 20% | 20 | 20 |
| Hit #2 — Fluent Bit DaemonSet + pipeline + JSON parseado | 20% | 19 | 20 |
| Hit #3 — ILM policy (3 fases) + index template | 15% | 15 | 15 |
| Hit #4 — KQL cookbook (6 queries) | 15% | 14 | 15 |
| Hit #5 — Dashboard NDJSON importado as-code | 20% | 3 | 20 |
| ADR `0009-stack-de-logging-efk.md` | 10% | 9 | 10 |
| **TOTAL** | **100%** | **80** | **100** |
| Bonus Hit #6 — Alertas Kibana | +5% | 0 | +5 |
| Penalizaciones (Fluentd / Loki roto) | | 0 | — |

### Nota Final TP2 Parte 2: **8.0 / 10**

---

## Devolución General

**Fortalezas:**
```
ECK + ES + Kibana perfectamente configurados — versiones, CRDs, ILM, resources. Todo correcto.
Fluent Bit con TLS al cluster ECK bien resuelto (certificado montado via extraVolumes).
KQL cookbook con las 6 queries requeridas, bien documentadas con equivalente Lucene.
ADR 0009 con mediciones reales y ELv2 bien explicada.
```

**Puntos a mejorar:**
```
Hit #5 dashboard (−17 pts): el NDJSON es un placeholder textual. Es el único entregable
importante pendiente de esta parte. Para completarlo:
  1. Crear el dashboard en Kibana con los 6 paneles requeridos
  2. Saved Objects → Export → "Include related objects" → descargar como NDJSON
  3. Guardar en efk/dashboards/scraper-overview.ndjson
  4. Agregar en install.sh el import via POST /api/saved_objects/_import

OpenSearch en ADR 0009 (−1 pt): agregar una línea nombrando el fork de AWS como
ejemplo concreto de cómo el riesgo de licencia ELv2 ya se materializó.
```

**Comentarios para el grupo:**
```
La infraestructura EFK está correcta y completa — ECK, ILM, Fluent Bit, KQL cookbook.
Los −20 puntos son de un solo entregable (el dashboard NDJSON) que fue marcado como
placeholder y nunca completado. Con el dashboard real, esta parte sería un 10.
El dashboard de Kibana ya tiene los datos para generarlo — solo falta exportarlo.
```
