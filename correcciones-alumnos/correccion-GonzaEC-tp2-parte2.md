# Corrección TP2 — Parte 2: Logging centralizado con EFK (Elasticsearch + Fluent Bit + Kibana)

**Grupo:** ONE
**Integrantes:**
- Anito, Cristian
- Soto, Roberto
- Claros, Federico
- Romero, Nicolas
- Buzzo Marcelo, Rocco
- Echeverria Crenna, Gonzalo
**Repo GitHub:** https://github.com/GonzaEC/TP2-SIP
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
| B3 | `install.sh` levanta el stack completo desde cero en cluster limpio | ✅ OK | `set -euo pipefail`, helm --wait, health checks |
| B4 | Versiones pinneadas: ECK `2.16.x`, ES/Kibana `8.17.x`, Fluent Bit `3.2.x` — NO `latest` | ✅ OK | ECK 2.16.0, ES/Kibana 8.17.3, Fluent Bit 3.2.4 |
| B5 | NO usa Fluentd (usa Fluent Bit) | ✅ OK | fluent/fluent-bit:3.2.4 — chart 0.48.5 |
| B6 | NO usa chart deprecado `elastic/elasticsearch` — sólo ECK Operator | ✅ OK | elastic/eck-operator 2.16.0, CRDs `elasticsearch.k8s.elastic.co/v1` |
| B7 | `gitleaks detect` da 0 leaks (sin password elastic ni webhook Discord en repo) | ✅ OK | ECK auto-genera passwords; Discord via env var |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | TESTING.md incluye checklist |

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
| Existe carpeta `efk/` con `README.md` (separada de `observability/`) | 1 | 1 | README 8,720 bytes ✓ |
| Existen `helm/eck-operator-values.yaml` y `helm/fluent-bit-values.yaml` | 1 | 1 | ✓ |
| Existen `manifests/namespace.yaml`, `elasticsearch.yaml`, `kibana.yaml`, `kibana-nodeport.yaml`, `ilm-policy.json` | 1 | 1 | Todos presentes ✓ |
| Existe `efk/install.sh` idempotente con todos los pasos | 1 | 1 | 7,169 bytes, completo ✓ |

**Subtotal 1.1:** 4 / 4

### 1.2 ECK Operator y CRDs (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| ECK Operator instalado via chart `elastic/eck-operator` versión `2.16.x` | 2 | 2 | 2.16.0 ✓ |
| CR `Elasticsearch` definido via CRD `elasticsearch.k8s.elastic.co/v1` (no chart legacy) | 2 | 2 | ✓ |
| Resources ECK Operator dentro de límites (≤ 100m CPU, ≤ 256Mi RAM) | 1 | 1 | 50-100m CPU, 128-256Mi ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Elasticsearch (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Version `8.17.x` declarada en el CR | 1 | 1 | 8.17.3 ✓ |
| `number_of_replicas: 0` en el index template (evita estado `yellow` en single-node) | 2 | 2 | Configurado en index template; `node.store.allow_mmap: false` adicional ✓ |
| Resources dentro de límites: requests ≤ 1Gi RAM / limits ≤ 2Gi RAM; PVC 10Gi `local-path` | 2 | 2 | Heap 768MB, límite 1.5GB; PVC 10Gi ✓ |

**Subtotal 1.3:** 5 / 5

### 1.4 Kibana (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CR `Kibana` definido via CRD, versión `8.17.x` | 1 | 1 | 8.17.3 ✓ |
| Service NodePort 30001 funcional | 1 | 1 | kibana-nodeport.yaml ✓ |
| Resources dentro de límites (≤ 500m CPU, ≤ 1Gi RAM) | 1 | 1 | 512Mi-1Gi ✓ |
| Password del usuario `elastic` gestionada por ECK (no commiteada) | 1 | 1 | Auto-generada por ECK, accedida vía kubectl get secret ✓ |

**Subtotal 1.4:** 4 / 4

### 1.5 Verificación de funcionamiento (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Elasticsearch status = `green` tras `install.sh` (evidencia en video) | 1 | 1 | hit1-Output.png ✓ |
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
| Resources dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 1 | 64-128Mi ✓ |

**Subtotal 2.1:** 5 / 5

### 2.2 Pipeline Input → Parser → Filter → Output (10 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Input `kubernetes` configurado leyendo de `/var/log/containers/` | 2 | 2 | Tail input → `*ml-scraper*.log` con CRI parser ✓ |
| Parser JSON correcto (parsea el JSON del scraper emitido por `logging_setup.py`) | 3 | 3 | CRI parser + JSON/regex parsing pipeline; Lua para extracción ✓ |
| Filter `Kubernetes` para enriquecer con metadata (namespace, pod, labels) | 2 | 2 | kubernetes enrichment filter ✓ |
| Output Elasticsearch apuntando al cluster ECK con TLS (cert montado via extraVolumes) | 3 | 3 | HTTPS a scraper-es-http.elastic.svc; certs via extraVolumes ✓ |

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
| Existe `efk/manifests/ilm-policy.json` commiteado | 1 | 1 | 652 bytes ✓ |
| Policy tiene 3 fases: `hot` → `warm` → `delete` | 2 | 2 | ✓ |
| Fase `hot`: rollover por `max_age: 1d` o `max_primary_shard_size: 1gb` | 2 | 2 | max_age 1d + max_primary_shard_size 1GB ✓ |
| Fase `delete`: `min_age: 7d` (retención total = 7 días) | 2 | 2 | Retención total 7 días ✓ |

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
| Data view `scraper-logs` con index pattern `scraper-logs-*` y timestamp `@timestamp` creado | 2 | 2 | Incluida en NDJSON exportado ✓ |
| Policy `scraper-logs` visible en Kibana → Stack Management → Index Lifecycle Policies (evidencia) | 1 | 1 | hit3-ilm-policy.png ✓ |
| Policy aplicada en `install.sh` via API curl (no manual en UI) | 1 | 1 | `POST /_ilm/policy/scraper-logs` en install.sh ✓ |

**Subtotal 3.3:** 4 / 4

**TOTAL HIT #3:** 15 / 15

---

## HIT #4 — Cookbook KQL: 6+ queries útiles (15 puntos)

### 4.1 Archivo y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/queries/kql-cookbook.md` | 1 | 1 | 10,451 bytes ✓ |
| Usa KQL exclusivamente (no `language: lucene`) | 1 | 1 | KQL con equivalentes Lucene documentados ✓ |
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
| El cookbook menciona explícitamente diferencias con las queries de Parte 1 (KQL vs LogQL) | 2 | 1 | Compara KQL vs Lucene con notas de performance (O(1) keyword, O(n) wildcard). La comparación explícita con LogQL de Parte 1 no es directa. |

**Subtotal 4.3:** 1 / 2

### Observaciones Hit #4
```
Cookbook excelente en calidad y variedad. El único gap es la comparación directa KQL vs LogQL
(modelo label-first vs full-text) que ayudaría a preparar el argumento para la Parte 4.
```

**TOTAL HIT #4:** 14 / 15

---

## HIT #5 — Dashboard Kibana provisionado as-code (NDJSON + import API) (20 puntos)

### 5.1 Provisioning as-code (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `efk/dashboards/scraper-overview.ndjson` commiteado | 2 | 2 | 11,777 bytes ✓ |
| NDJSON exportado con "Include related objects" (data view + visualizaciones incluidas) | 2 | 2 | Data View incluida en NDJSON ✓ |
| `install.sh` importa el NDJSON via `POST /api/saved_objects/_import` con header `kbn-xsrf: true` | 3 | 3 | `curl -H "kbn-xsrf: true"` confirmado ✓ |
| Password de elastic obtenida por `kubectl get secret` (no hardcodeada en el script) | 1 | 1 | `kubectl get secret scraper-es-elastic-user` ✓ |

**Subtotal 5.1:** 8 / 8

### 5.2 Contenido del dashboard — mínimo 6 paneles (8 pts)

| Panel | Presente | Datos reales | Pts |
|-------|----------|-------------|-----|
| Metric — Total de eventos hoy | ✅ | ✅ | 1 |
| Metric — % eventos `level: "ERROR"` vs total | ✅ | ✅ | 1 |
| Bar chart — Top 5 productos con más errores | ✅ | ✅ | 2 |
| Pie chart — Distribución por `level` (INFO / WARNING / ERROR) | ✅ | ✅ | 2 |
| Line chart — Eventos por minuto last 6h, breakdown por `level` | ✅ | ✅ | 1 |
| Table — Última corrida exitosa por producto | ✅ | ✅ | 1 |

**Subtotal 5.2:** 8 / 8

### 5.3 Calidad del NDJSON (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| NDJSON parseable sin errores (no JSON roto) | 1 | 1 | ✓ |
| Import retorna `"success": true` (evidencia en video o log) | 2 | 2 | hit5-dashboard.png ✓ |
| Dashboard visible en Kibana → Dashboards con datos reales (no "No results found") | 1 | 1 | ✓ |

**Subtotal 5.3:** 4 / 4

**TOTAL HIT #5:** 20 / 20

---

## ADR — `0009-stack-de-logging-efk.md` (10 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0009-stack-de-logging-efk.md` (numeración continua) | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| Extensión adecuada (no genérico ni copiado de la consigna) | 1 | 1 | 1,743 bytes, razonamiento propio ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Compara footprint real medido en el cluster (Loki ≈ 256Mi vs ES ≈ 2Gi) | 2 | 2 | ~2.5-3GB ES vs <1GB Loki ✓ |
| Compara latencia de query (full-text search de ES vs label-first de Loki) | 2 | 2 | Lucene full-text vs label-first ✓ |
| Menciona licencia Elastic License v2 (ELv2) y que NO es OSS-OSI + alternativa OpenSearch | 2 | 0 | Solo menciona "commercial licensing" de forma genérica. No cita ELv2 (2021), ni SSPL, ni el fork OpenSearch como consecuencia. **Gap importante.** |
| Conclusión abierta — no sentencia cuál es mejor, remite a Parte 4 para el ADR comparativo | 1 | 1 | "gather comparative performance data" ✓ |

**Subtotal 6.2:** 5 / 7

### Observaciones ADR
```
El ADR omite la historia de licenciamiento de Elastic: cambio a ELv2 en 7.11 (2021),
incompatibilidad OSS-OSI, y el fork OpenSearch de AWS. Esto es relevante para evaluar
el riesgo de lock-in, que es el argumento central del ADR 0010 (Parte 3) y 0012 (Parte 4).
```

**TOTAL ADR:** 8 / 10

---

## BONUS — Hit #6: Alertas via Kibana Alerting (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Connector Discord configurado via Webhook (URL por env var, no commiteada) | 1 | 1 | DISCORD_WEBHOOK_URL env var ✓ |
| Rule type "Elasticsearch query" con KQL `level: "ERROR"`, threshold > 5, window 1h | 2 | 2 | create_alert_rule.py implementa la rule ✓ |
| Screenshot o evidencia de notificación recibida en Discord | 2 | 2 | hit6-discord-alert-efk.png, hit6-discord.png ✓ |

**TOTAL BONUS Hit #6:** 5 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 2

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — ECK + Elasticsearch (green) + Kibana | 20% | 20 | 20 |
| Hit #2 — Fluent Bit DaemonSet + pipeline + JSON parseado | 20% | 20 | 20 |
| Hit #3 — ILM policy (3 fases) + index template | 15% | 15 | 15 |
| Hit #4 — KQL cookbook (6 queries) | 15% | 14 | 15 |
| Hit #5 — Dashboard NDJSON importado as-code | 20% | 20 | 20 |
| ADR `0009-stack-de-logging-efk.md` | 10% | 8 | 10 |
| **TOTAL** | **100%** | **97** | **100** |
| Bonus Hit #6 — Alertas Kibana | +5% | 5 | +5 |
| Penalizaciones (Fluentd / Loki roto) | | 0 | — |

### Nota Final TP2 Parte 2: 9.7 / 10 (con bonus: 10.2)

---

## Devolución General

**Fortalezas:**
```
ECK perfectamente implementado (green cluster, ECK-managed certs, ILM automático).
Fluent Bit con pipeline defensivo (CRI parser + JSON + Lua + fallbacks).
Dashboard auto-importado con kbn-xsrf header correcto — detalle que muchos omiten.
```

**Puntos a mejorar:**
```
ADR 0009: agregar la historia de licenciamiento de Elastic (ELv2 2021, OpenSearch fork).
Este contexto es clave para el argumento de lock-in en la Parte 4.
KQL cookbook: agregar una sección comparando KQL vs LogQL explícitamente
(modelo label-first vs full-text) — útil para la matriz de decisión de Parte 4.
```

**Comentarios para el grupo:**
```
La implementación técnica es prácticamente perfecta. El gap está en la documentación
del riesgo de licenciamiento de Elastic, que es un punto que la cátedra va a preguntar
en la defensa de Parte 4. Recomendamos actualizar el ADR 0009 antes de esa instancia.
```
