# Corrección TP2 — Parte 3: OpenTelemetry Collector + SDK + multi-backend

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
**Fecha de corrección:** 2026-05-09 (re-corrección: 2026-05-11)
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) | ✅ OK | Parte 1: 9.7/10 |
| B2 | TP2 · Parte 2 entregada y aprobada (≥ 60/100) | ✅ OK | Parte 2: 9.6/10 |
| B3 | Existe `otel/install.sh` ejecutable | ✅ OK | |
| B4 | `otel/install.sh` funciona sobre cluster con Loki + EFK preexistentes | ✅ OK | Verifica existencia de namespaces observability y elastic |
| B5 | Helm charts pinneados a versiones específicas (no `latest`) | ✅ OK | OTel Operator 0.74.0, cert-manager 1.16.1, Jaeger 3.4.0 |
| B6 | Usa distribución `contrib` del collector — NO `core` | ✅ OK | `otel/opentelemetry-collector-contrib:0.110.0` ✓ |
| B7 | `gitleaks detect` da 0 leaks | ✅ OK | CI con gitleaks-action; creds via secrets |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | CI + README |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

---

## HIT #1 — Deploy del OpenTelemetry Operator (10 puntos)

### 1.1 Estructura del repositorio (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe carpeta `otel/` con `README.md`, `helm/`, `manifests/`, `scraper-instrumentation/`, `install.sh` | 1 | 1 | Todos presentes ✓ |
| Existe `otel/helm/otel-operator-values.yaml` con resources definidos | 1 | 1 | ✓ |
| Existe `otel/manifests/namespace.yaml`, `collector-agent.yaml`, `rbac.yaml`, `scraper-otlp-config.yaml` | 1 | 1 | ✓ |

**Subtotal 1.1:** 3 / 3

### 1.2 Operator e instalación (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Chart `open-telemetry/opentelemetry-operator` versión `0.74.x` (no `latest`) | 2 | 2 | 0.74.0 ✓ |
| cert-manager presente como prerequisito | 1 | 1 | 1.16.1 con installCRDs ✓ |
| Resources del operator dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 1 | 64-128Mi ✓ |
| `watchNamespace: ""` configurado (operator ve todos los namespaces) | 1 | 1 | Default all-namespaces ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Verificación de CRDs (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CRD `opentelemetrycollectors.opentelemetry.io` presente en el cluster | 1 | 1 | ✓ |
| Operator pod `Running` en `otel-operator-system` (evidencia en video) | 1 | 1 | hit2-debug-output.png ✓ |

**Subtotal 1.3:** 2 / 2

**TOTAL HIT #1:** 10 / 10

---

## HIT #2 — OpenTelemetryCollector en modo DaemonSet (15 puntos)

### 2.1 CR OpenTelemetryCollector (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Manifiesto `collector-agent.yaml` define CR `kind: OpenTelemetryCollector` | 2 | 2 | ✓ |
| `mode: daemonset` configurado | 1 | 1 | ✓ |
| Imagen `otel/opentelemetry-collector-contrib:0.110.x` (no `core`, no `latest`) | 2 | 2 | 0.110.0 ✓ |
| Tolerations para nodo control-plane k3s (single-node) | 1 | 1 | `operator: Exists` NoSchedule ✓ |

**Subtotal 2.1:** 6 / 6

### 2.2 Pipeline receivers → processors → exporters (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Receiver `filelog` configurado leyendo `/var/log/pods/ml-scraper_*` | 2 | 2 | `/var/log/pods/ml-scraper_*/*/*.log` ✓ |
| Processor `batch` configurado | 1 | 1 | 10s timeout, 1024 batch size ✓ |
| Processor `k8sattributes` configurado | 2 | 2 | namespace, pod, deployment, cronjob, job, node + labels ✓ |
| Service pipeline conecta receivers → processors → exporters correctamente | 2 | 2 | logs: filelog+otlp → k8sattributes,attributes,transform,batch → loki,elasticsearch; traces: otlp → jaeger ✓ |

**Subtotal 2.2:** 7 / 7

### 2.3 RBAC (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| `rbac.yaml` con ServiceAccount + ClusterRole para `k8sattributes` | 2 | 2 | SA + ClusterRole + ClusterRoleBinding para pods, namespaces, nodes, daemonsets, statefulsets, deployments, jobs, cronjobs ✓ |

**Subtotal 2.3:** 2 / 2

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — Fan-out simultáneo a Loki + Elasticsearch (25 puntos)

### 3.1 Exporters configurados (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Exporter `otlphttp/loki` apuntando a `http://loki.observability.svc.cluster.local:3100` | 3 | 3 | `/otlp` endpoint ✓ |
| Exporter `elasticsearch` apuntando al cluster ECK con credenciales | 3 | 3 | `scraper-es-http.elastic.svc.cluster.local:9200`, auth via secret ✓ |
| Secret de elastic copiado de `elastic` a `otel` en `install.sh` (no hardcodeado) | 2 | 2 | `kubectl get secret ... | sed ... | kubectl apply` ✓ |

**Subtotal 3.1:** 8 / 8

### 3.2 Verificación de fan-out (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper aparecen en Loki / Grafana Explore | 4 | 4 | hit3-fanout-loki.png ✓ |
| Logs del scraper aparecen en Elasticsearch / Kibana Discover | 4 | 4 | hit3-fanout-elastic.png ✓ |
| Mismo `log_id` (o campo único) identificable en ambos backends | 4 | 4 | UUID generado por processor `transform` visible en ambos ✓ |

**Subtotal 3.2:** 12 / 12

### 3.3 Screenshots de evidencia (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit3-fanout-loki.png` con el `log_id` visible | 2 | 2 | ✓ |
| Existe `otel/screenshots/hit3-fanout-elastic.png` con el mismo `log_id` visible | 2 | 2 | ✓ |
| Los dos screenshots corresponden al mismo evento (mismo timestamp razonable) | 1 | 1 | ✓ |

**Subtotal 3.3:** 5 / 5

**TOTAL HIT #3:** 25 / 25

---

## HIT #4 — Promtail + Fluent Bit escalados a 0 (15 puntos)

### 4.1 Escalado a 0 (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Promtail DaemonSet en namespace `observability` escalado a 0 | 3 | 3 | `install.sh` incluye el escalado ✓ |
| Fluent Bit DaemonSet en namespace `elastic` escalado a 0 | 3 | 3 | `install.sh` incluye el escalado ✓ |

**Subtotal 4.1:** 6 / 6

### 4.2 Continuidad del flujo sin agentes legacy (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper siguen llegando a Loki después de bajar Promtail | 3 | 3 | ✓ |
| Logs del scraper siguen llegando a Elasticsearch después de bajar Fluent Bit | 3 | 3 | ✓ |

**Subtotal 4.2:** 6 / 6

### 4.3 Screenshot y documentación (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit4-old-agents-down.png` mostrando DaemonSets con 0 pods | 2 | 2 | ✓ |
| `install.sh` incluye el escalado a 0 (no manual post-instalación) | 1 | 1 | ✓ |

**Subtotal 4.3:** 3 / 3

**TOTAL HIT #4:** 15 / 15

---

## HIT #5 — Scraper instrumentado con SDK Python (20 puntos)

> **NOTA:** El scraper en este repo es Node.js, no Python. La implementación usa OTel JavaScript SDK con Winston instrumentation. `otel/scraper-instrumentation/otel_setup.js` presente.

### 5.1 Dependencias OTel (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/requirements-otel.txt` con versiones pinneadas `1.30.x` | 1 | 0 | Es JavaScript — no hay requirements-otel.txt. Equivalente sería package.json. No commiteado en `otel/scraper-instrumentation/`. |
| `opentelemetry-sdk==1.30.x`, `opentelemetry-exporter-otlp-proto-grpc==1.30.x` en `requirements.txt` | 2 | 0 | No Python SDK. Penalización por no seguir stack requerido. |

**Subtotal 5.1:** 0 / 3

### 5.2 Módulo `otel_setup.py` (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/otel_setup.py` con `LoggerProvider` + `BatchLogRecordProcessor` + `OTLPLogExporter` | 3 | 2 | `otel_setup.js` con `NodeSDK`, `SimpleLogRecordProcessor`, `OTLPLogExporter` — equivalente funcional en JS ✓ |
| `TracerProvider` configurado | 2 | 2 | `SimpleSpanProcessor` + `OTLPTraceExporter` ✓ |
| Lee `OTEL_EXPORTER_OTLP_ENDPOINT` de env var | 1 | 1 | ✓ vía ConfigMap |
| `Resource.create()` con `service.name`, `service.version` | 1 | 1 | `resourceFromAttributes({ SERVICE_NAME: 'scraper' })` ✓ |
| `atexit.register(logger_provider.shutdown)` o equivalente | 1 | 1 | SIGTERM, SIGINT y beforeExit handlers ✓ |

**Subtotal 5.2:** 7 / 8

### 5.3 ConfigMap de endpoint + CronJob actualizado (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/manifests/scraper-otlp-config.yaml` ConfigMap con `OTEL_EXPORTER_OTLP_ENDPOINT` usando `NODE_IP` | 2 | 2 | `http://$(NODE_IP):4317`, `OTEL_SERVICE_NAME: scraper` ✓ |
| CronJob del scraper actualizado con `env.NODE_IP` via `fieldRef: status.hostIP` + `envFrom: configMapRef` | 2 | 2 | ✓ |
| Imagen del scraper re-publicada con tag diferenciado (ej: `scraper:otel-v1`) | 1 | 0 | No evidenciado |

**Subtotal 5.3:** 4 / 5

### 5.4 Verificación SDK (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Log records en Loki/Kibana tienen `trace_id` no vacío (evidencia en video — query LogQL o KQL) | 3 | 3 | hit5-otlp-trace.png muestra traces activos ✓ |
| Log records tienen `span_id` no vacío | 1 | 1 | ✓ (con TracerProvider activo y traces en Jaeger) |

**Subtotal 5.4:** 4 / 4

### Observaciones Hit #5
```
Implementación JavaScript en lugar de Python. La funcionalidad es equivalente:
NodeSDK con OTLPLogExporter + OTLPTraceExporter, WinstonInstrumentation, handlers
de shutdown apropiados. La principal penalización es la falta de requirements-otel.txt
y el uso de JS en lugar de Python como requiere la consigna.

Trace_id poblado evidenciado por hit5-otlp-trace.png — esto distingue a este grupo
del grupo ONE donde el trace_id estaba vacío.
```

**TOTAL HIT #5:** 15 / 20

---

## ADR — `0010-instrumentacion-vendor-neutral.md` (15 puntos)

> **RE-CORRECCIÓN 2026-05-11:** Archivo entregado en push del 14 de mayo.

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0010-instrumentacion-vendor-neutral.md` (numeración continua) | 1 | 1 | ✓ entregado 2026-05-14 |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| No es genérico / copiado de la consigna — refleja el razonamiento del equipo | 1 | 1 | ~1294 palabras con razonamiento propio ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona lock-in con Grafana Labs (Promtail) y Elastic (Fluent Bit → ES) como motivación | 3 | 3 | "lock-in incipiente... Elastic cambió su licencia de Apache 2.0 a SSPL+ELv2" ✓ |
| Menciona costo operativo de mantener 2 agentes por nodo vs 1 colector OTel | 3 | 3 | "Reemplazamos 2 DaemonSets por 1 ... en producción con 20 nodos son 3 GB de RAM perdidos en agentes redundantes" ✓ |
| Menciona adopción de OTLP por los 4 grandes SaaS (Datadog, New Relic, Dynatrace, Splunk) | 3 | 3 | "los 4 grandes proveedores SaaS (Datadog, New Relic, Dynatrace, Splunk) ... soportan OTLP nativo" ✓ |
| Menciona la inversión de re-instrumentar el scraper y por qué paga a mediano plazo | 2 | 2 | "Re-instrumentar el scraper ahora cuesta ~4 horas ... El costo de esperar es bajo, el de migrar después es alto" ✓ |
| Remite al ADR comparativo de Parte 4 para la decisión final | 1 | 1 | Front-matter: "Referenced by: 0012 (stack final de observabilidad)" ✓ |

**Subtotal 6.2:** 12 / 12

### Observaciones ADR
```
ADR 0010 excelente. Todos los criterios cubiertos con cifras concretas (3 GB RAM
en 20 nodos, 4h de re-instrumentación vs. semanas después). Los 4 vendors SaaS
nombrados explícitamente. Razonamiento de costo de oportunidad bien articulado.
```

**TOTAL ADR:** 15 / 15

---

## BONUS — Hit #6: Traces visibles en Jaeger (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Backend de traces desplegado: Jaeger `jaegertracing/jaeger` v`3.4.x` (o Grafana Tempo) en namespace `otel` | 1 | 1 | Jaeger 3.4.0, NodePort 30002 ✓ |
| Exporter OTLP/traces en el collector apuntando al backend | 1 | 1 | `otlp/jaeger → jaeger-collector.otel.svc.cluster.local:4317` ✓ |
| Spans del scraper visibles en la UI de Jaeger/Tempo — screenshot | 2 | 2 | hit6-trace-jaeger.png ✓ |
| Existe ADR `0011-traces-vs-solo-logs.md` justificando por qué traces además de logs | 1 | 1 | ✓ entregado 2026-05-14 — ~724 palabras, cita M3 latency data y ADRs 0010 + 0012 |

**TOTAL BONUS Hit #6:** 5 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 3

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — OTel Operator + CRDs | 10% | 10 | 10 |
| Hit #2 — Collector DaemonSet + pipeline + k8sattributes | 15% | 15 | 15 |
| Hit #3 — Fan-out Loki + ES con log_id matching ⭐ | 25% | 25 | 25 |
| Hit #4 — Promtail + Fluent Bit a 0, flujo intacto | 15% | 15 | 15 |
| Hit #5 — SDK Python, trace_id populado | 20% | 15 | 20 |
| ADR `0010-instrumentacion-vendor-neutral.md` | 15% | 15 | 15 |
| **TOTAL** | **100%** | **95** | **100** |
| Bonus Hit #6 — Traces en Jaeger + ADR 0011 | +5% | 5 | +5 |

### Nota Final TP2 Parte 3: **9.5 / 10 (10.0 con bonus)**

> Re-corrección 2026-05-11: ADR 0010 entregado (+15 pts) y ADR 0011 entregado (+1 pt bonus). Nota original 8.0/10 → 9.5/10.

---

## Devolución General

**Fortalezas:**
```
Hit #1-4 perfectos: 65/65 pts. Collector bien diseñado con 3 pipelines (logs→loki,
logs→elastic, traces→jaeger). Jaeger funcionando con traces reales en UI.
Trace_id poblado en logs — diferencia crítica respecto a otros grupos.
otel_setup.js con shutdown handlers correctos y service.name configurado.
```

**Puntos a mejorar:**
```
Hit #5: único gap restante. Usar Python SDK (opentelemetry-sdk==1.30.x) como
requiere la consigna, o agregar package.json con versiones pinneadas del SDK JS.
Los -5 pts de esta sección no se recuperan, pero la nota final ya es excelente.
```

**Comentarios para el grupo:**
```
Re-corrección post-entrega: ADR 0010 y ADR 0011 entregados el 14 de mayo,
ambos de alta calidad. El ADR 0010 en particular —con los 4 vendors SaaS,
el cálculo de 3GB en 20 nodos y el ROI de re-instrumentación— es el mejor
de los cuatro grupos. La infraestructura OTel más el ADR 0010 hacen de esta
parte la más completa del grupo.
```
