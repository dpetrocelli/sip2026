# Corrección TP2 — Parte 2: Logging centralizado con EFK (Elasticsearch + Fluent Bit + Kibana)

**Grupo:** Systeam
**Integrantes:**
- Hoffmann, Axel
- Babino, Abril
- Avila, Tobias
- Collazo, Naiara
- Nomico, Mateo
- Casal, Ulises
**Repo GitHub:** https://github.com/UlisesCasal/SIP-Selenium-Systeam
**Video (YouTube):** _______________________________________________
**Fecha de entrega:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) — Loki sigue corriendo en `observability` | ✅ OK | Parte 1: 9.7/10 |
| B2 | Existe `efk/install.sh` ejecutable (carpeta separada de `observability/`) | ✅ OK | |
| B3 | `install.sh` levanta el stack completo desde cero en cluster limpio | ✅ OK | Idempotente con helm --wait y kubectl wait --for=jsonpath |
| B4 | Versiones pinneadas: ECK `2.16.x`, ES/Kibana `8.17.x`, Fluent Bit `3.2.x` — NO `latest` | ✅ OK | ECK 2.16.0, ES/Kibana 8.17.3, Fluent Bit 3.2.4 |
| B5 | NO usa Fluentd (usa Fluent Bit) | ✅ OK | fluent/fluent-bit:3.2.4 ✓ |
| B6 | NO usa chart deprecado `elastic/elasticsearch` — sólo ECK Operator | ✅ OK | elasticsearch.k8s.elastic.co/v1 CRD ✓ |
| B7 | `gitleaks detect` da 0 leaks | ✅ OK | CI con gitleaks-action; ECK auto-genera passwords |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | CI + README checklist |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

**Penalizaciones automáticas:**

| Penalización | Descuento | Aplica |
|---|---|---|
| Usa Fluentd en lugar de Fluent Bit | -5 pts | ☐ NO |
| Parte 1 rota / Loki no corre al momento de evaluar | -10 pts | ☐ NO |

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
| Resources ECK Operator dentro de límites (≤ 100m CPU, ≤ 256Mi RAM) | 1 | 1 | 50-100m / 128-256Mi ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Elasticsearch (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Version `8.17.x` declarada en el CR | 1 | 1 | 8.17.3 ✓ |
| `number_of_replicas: 0` en el index template (evita estado `yellow` en single-node) | 2 | 2 | Configurado en index template + `node.store.allow_mmap: false` ✓ |
| Resources dentro de límites: requests ≤ 1Gi RAM / limits ≤ 2Gi RAM; PVC 10Gi `local-path` | 2 | 2 | 1Gi req / 2Gi limit; PVC 10Gi ✓ |

**Subtotal 1.3:** 5 / 5

### 1.4 Kibana (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CR `Kibana` definido via CRD, versión `8.17.x` | 1 | 1 | 8.17.3 ✓ |
| Service NodePort 30001 funcional | 1 | 1 | kibana-nodeport.yaml ✓ |
| Resources dentro de límites (≤ 500m CPU, ≤ 1Gi RAM) | 1 | 1 | 200-500m / 512Mi-1Gi ✓ |
| Password del usuario `elastic` gestionada por ECK (no commiteada) | 1 | 1 | Auto-generada ECK; recuperada via kubectl ✓ |

**Subtotal 1.4:** 4 / 4

### 1.5 Verificación de funcionamiento (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Elasticsearch status = `green` tras `install.sh` (evidencia en video) | 1 | 1 | install.sh usa `kubectl wait --for=jsonpath` ✓ |
| Kibana status = `available` y accesible en :30001 (evidencia en video) | 1 | 1 | ✓ |

**Subtotal 1.5:** 2 / 2

**TOTAL HIT #1:** 20 / 20

---

## HIT #2 — Fluent Bit como DaemonSet, pipeline al scraper (20 puntos)

### 2.1 Instalación y configuración base (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Chart `fluent/fluent-bit` versión `0.48.x`, imagen tag `3.2.x` (no `latest`) | 2 | 2 | 0.48.5 / 3.2.4 ✓ |
| DaemonSet running con `tolerations` para nodo control-plane k3s (single-node) | 1 | 1 | `operator: Exists` NoSchedule ✓ |
| RBAC configurado (`serviceAccount.create: true`, `rbac.create: true`) | 1 | 1 | ✓ |
| Resources dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 1 | 64Mi / 128Mi ✓ |

**Subtotal 2.1:** 5 / 5

### 2.2 Pipeline Input → Parser → Filter → Output (10 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Input `kubernetes` configurado leyendo de `/var/log/containers/` | 2 | 2 | Tail input `*ml-scraper*.log` con CRI parser ✓ |
| Parser JSON correcto (parsea el JSON del scraper) | 3 | 3 | CRI parser + json_scraper custom parser ✓ |
| Filter `Kubernetes` para enriquecer con metadata (namespace, pod, labels) | 2 | 2 | Kubernetes filter + Grep `app=scraper` ✓ |
| Output Elasticsearch apuntando al cluster ECK con TLS (cert montado via extraVolumes) | 3 | 3 | HTTPS; TLS cert via extraVolumes; auth via secret ✓ |

**Subtotal 2.2:** 10 / 10

### 2.3 Evidencia de indexado (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Índices `scraper-logs-*` aparecen en Elasticsearch (evidencia en video/Kibana) | 3 | 3 | hit2-fluentbit-discover.png ✓ |
| Campos JSON del scraper visibles como fields en Kibana Discover (no como string crudo) | 2 | 2 | ✓ |

**Subtotal 2.3:** 5 / 5

**TOTAL HIT #2:** 20 / 20

---

## HIT #3 — Index pattern + ILM (rollover, retention 7 días) (15 puntos)

### 3.1 ILM policy (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/manifests/ilm-policy.json` commiteado | 1 | 1 | ✓ |
| Policy tiene 3 fases: `hot` → `warm` → `delete` | 2 | 2 | ✓ |
| Fase `hot`: rollover por `max_age: 1d` o `max_primary_shard_size: 1gb` | 2 | 2 | max_age 1d + max_primary_shard_size 1GB ✓ |
| Fase `delete`: `min_age: 7d` (retención total = 7 días) | 2 | 2 | 7-day total retention ✓ |

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
| Data view `scraper-logs` con index pattern `scraper-logs-*` y timestamp `@timestamp` creado | 2 | 2 | Incluida en NDJSON ✓ |
| Policy `scraper-logs` visible en Kibana → Stack Management → ILM (evidencia) | 1 | 1 | hit3-ilm-policy.png ✓ |
| Policy aplicada en `install.sh` via API curl (no manual en UI) | 1 | 1 | `PUT /_ilm/policy/scraper-logs` en install.sh ✓ |

**Subtotal 3.3:** 4 / 4

**TOTAL HIT #3:** 15 / 15

---

## HIT #4 — Cookbook KQL: 6+ queries útiles (15 puntos)

### 4.1 Archivo y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/queries/kql-cookbook.md` | 1 | 1 | ✓ |
| Usa KQL exclusivamente (no `language: lucene`) | 1 | 1 | KQL con Lucene equivalentes documentados ✓ |
| Cada query documenta: pregunta · KQL · equivalente Lucene · por qué | 1 | 1 | Análisis técnico de field types + performance ✓ |

**Subtotal 4.1:** 3 / 3

### 4.2 Queries obligatorias (10 pts)

| Query | Presente | KQL correcto | Funciona | Pts |
|-------|----------|-------------|----------|-----|
| Q1 — Errores por producto últimas 24h | ✅ | ✅ | ✅ | 2 |
| Q2 — Top selectores faltantes | ✅ | ✅ | ✅ | 2 |
| Q3 — Distribución duración del Job (`event: "scrape_completado"`) | ✅ | ✅ | ✅ | 2 |
| Q4 — Timeouts de Selenium (`message: *timeout*`) | ✅ | ✅ | ✅ | 1 |
| Q5 — Eventos de CronJob específico por `kubernetes.labels.job_name` | ✅ | ✅ | ✅ | 1 |
| Q6 — Errores excluyendo módulo Postgres | ✅ | ✅ | ✅ | 2 |

**Subtotal 4.2:** 10 / 10

### 4.3 Comparativa KQL vs LogQL (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| El cookbook menciona explícitamente diferencias con las queries de Parte 1 (KQL vs LogQL) | 2 | 1 | Compara KQL vs Lucene con análisis de performance (O(1) keyword, O(n) wildcard). La comparación directa KQL vs LogQL (modelo label-first) no está presente. |

**Subtotal 4.3:** 1 / 2

### Observaciones Hit #4
```
Cookbook de alta calidad técnica con análisis de tipos de campos y performance.
El único gap: no hay comparación directa contra el cookbook LogQL de Parte 1.
Añadir una sección "KQL vs LogQL" refuerza el argumento para la Parte 4.
```

**TOTAL HIT #4:** 14 / 15

---

## HIT #5 — Dashboard Kibana provisionado as-code (NDJSON + import API) (20 puntos)

### 5.1 Provisioning as-code (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/dashboards/scraper-overview.ndjson` commiteado | 2 | 2 | 17.3 KB ✓ |
| NDJSON exportado con "Include related objects" (data view + visualizaciones incluidas) | 2 | 2 | Data View incluida ✓ |
| `install.sh` importa el NDJSON via `POST /api/saved_objects/_import` con header `kbn-xsrf: true` | 3 | 3 | ✓ (kbn-xsrf presente) |
| Password de elastic obtenida por `kubectl get secret` (no hardcodeada en el script) | 1 | 1 | ✓ |

**Subtotal 5.1:** 8 / 8

### 5.2 Contenido del dashboard — mínimo 6 paneles (8 pts)

| Panel | Presente | Datos reales | Pts |
|-------|----------|-------------|-----|
| Metric — Total de eventos hoy | ✅ | ✅ | 1 |
| Metric — % eventos `level: "ERROR"` vs total | ✅ | ✅ | 1 |
| Bar chart — Top 5 productos con más errores | ✅ | ✅ | 2 |
| Pie chart — Distribución por `level` | ✅ | ✅ | 2 |
| Line chart — Eventos por minuto last 6h | ✅ | ✅ | 1 |
| Table — Última corrida exitosa por producto | ✅ | ✅ | 1 |

**Subtotal 5.2:** 8 / 8

### 5.3 Calidad del NDJSON (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| NDJSON parseable sin errores (no JSON roto) | 1 | 1 | ✓ |
| Import retorna `"success": true` (evidencia en video o log) | 2 | 2 | hit5-dashboard.jpeg ✓ |
| Dashboard visible en Kibana → Dashboards con datos reales | 1 | 1 | ✓ |

**Subtotal 5.3:** 4 / 4

**TOTAL HIT #5:** 20 / 20

---

## ADR — `0009-stack-de-logging-efk.md` (10 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0009-stack-de-logging-efk.md` (numeración continua) | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| Extensión adecuada (no genérico ni copiado de la consigna) | 1 | 1 | 666 palabras, razonamiento propio ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Compara footprint real medido en el cluster (Loki ≈ 256Mi vs ES ≈ 2Gi) | 2 | 1 | Tabla de resources configurados (requests/limits). Son valores declarados en YAML, no footprint real medido con `kubectl top`. Parcialmente cumple. |
| Compara latencia de query (full-text search de ES vs label-first de Loki) | 2 | 0 | **`<medir>` placeholders**. El ADR dice "latencia a medir" pero no tiene valores reales. |
| Menciona licencia Elastic License v2 (ELv2) y que NO es OSS-OSI + alternativa OpenSearch | 2 | 2 | Sección dedicada a ELv2, incompatibilidad OSI ✓ |
| Conclusión abierta — no sentencia cuál es mejor, remite a Parte 4 para el ADR comparativo | 1 | 1 | "métricas a medir" y conclusión diferida ✓ |

**Subtotal 6.2:** 4 / 7

### Observaciones ADR
```
Punto positivo: sección dedicada a ELv2 — muy pocos grupos lo hacen.
Punto negativo: los campos <medir> en latencia de query indican que el ADR se escribió
antes de tomar las mediciones. Para la Parte 4 esto es un gap: el ADR 0009 debería tener
números reales para que el ADR 0012 los pueda citar.
```

**TOTAL ADR:** 7 / 10

---

## BONUS — Hit #6: Alertas via Kibana Alerting (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Connector Discord configurado via Webhook (URL por env var, no commiteada) | 1 | 0 | No hay evidencia de Kibana alerting en EFK |
| Rule type "Elasticsearch query" con KQL `level: "ERROR"`, threshold > 5, window 1h | 2 | 0 | No implementado |
| Screenshot o evidencia de notificación recibida en Discord | 2 | 0 | No hay hit6 screenshot en efk/ |

**TOTAL BONUS Hit #6:** 0 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 2

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — ECK + Elasticsearch (green) + Kibana | 20% | 20 | 20 |
| Hit #2 — Fluent Bit DaemonSet + pipeline + JSON parseado | 20% | 20 | 20 |
| Hit #3 — ILM policy (3 fases) + index template | 15% | 15 | 15 |
| Hit #4 — KQL cookbook (6 queries) | 15% | 14 | 15 |
| Hit #5 — Dashboard NDJSON importado as-code | 20% | 20 | 20 |
| ADR `0009-stack-de-logging-efk.md` | 10% | 7 | 10 |
| **TOTAL** | **100%** | **96** | **100** |
| Bonus Hit #6 — Alertas Kibana | +5% | 0 | +5 |
| Penalizaciones | | 0 | — |

### Nota Final TP2 Parte 2: 9.6 / 10

---

## Devolución General

**Fortalezas:**
```
ECK perfecto: número de replicas correcto, ILM 3 fases, kbn-xsrf, dashboard NDJSON 17.3KB.
ADR 0009 con sección explícita de ELv2 — único grupo que lo detalla correctamente.
Fluent Bit con dos parsers customizados (cri + json_scraper) — diseño robusto.
```

**Puntos a mejorar:**
```
ADR 0009: completar los placeholders <medir> con valores reales de kubectl top
y latencia de query. Sin esos números, el ADR 0012 de Parte 4 no tiene qué citar.

Bonus EFK: la alerta de Kibana (Hit #6 de Parte 2) no fue implementada.
Si se hace antes de la Parte 4, suma 5 pts.
```

**Comentarios para el grupo:**
```
Parte 2 técnicamente impecable. El gap está en la documentación analítica (ADR 0009
con placeholders), que va a perjudicar la Parte 4. Completar esas mediciones ahora
es esencial para que el ADR 0012 pueda citar datos propios.
```
