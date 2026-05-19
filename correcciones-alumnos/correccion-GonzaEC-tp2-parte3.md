# Corrección TP2 — Parte 3: OpenTelemetry Collector + SDK + multi-backend

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
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) — Loki corriendo en `observability` | ✅ OK | Parte 1: 9.7/10 |
| B2 | TP2 · Parte 2 entregada y aprobada (≥ 60/100) — EFK corriendo en `elastic` | ✅ OK | Parte 2: 9.7/10 |
| B3 | Existe `otel/install.sh` ejecutable (carpeta separada de `observability/` y `efk/`) | ✅ OK | |
| B4 | `otel/install.sh` funciona sobre cluster con Loki + EFK preexistentes | ✅ OK | Verifica existencia de namespaces observability y elastic |
| B5 | Helm charts pinneados a versiones específicas (no `latest`) | ✅ OK | OTel Operator 0.74.0, cert-manager 1.16.1 |
| B6 | Usa distribución `contrib` del collector (`otel/opentelemetry-collector-contrib`) — NO `core` | ✅ OK | `otel/opentelemetry-collector-contrib:0.110.0` ✓ |
| B7 | `gitleaks detect` da 0 leaks (sin endpoints con basic-auth embebido ni secrets) | ✅ OK | Creds copiadas entre namespaces, no hardcodeadas |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | TESTING.md |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

---

## HIT #1 — Deploy del OpenTelemetry Operator (10 puntos)

### 1.1 Estructura del repositorio (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe carpeta `otel/` con `README.md`, `helm/`, `manifests/`, `scraper-instrumentation/`, `install.sh` | 1 | 0 | Faltan `scraper-instrumentation/` directorio (ver Hit #5). Resto presente: README, helm/, manifests/, install.sh ✓ |
| Existe `otel/helm/otel-operator-values.yaml` con resources definidos | 1 | 1 | 269 bytes, resources definidos ✓ |
| Existe `otel/manifests/namespace.yaml`, `collector-agent.yaml`, `rbac.yaml`, `scraper-otlp-config.yaml` | 1 | 1 | Todos presentes ✓ |

**Subtotal 1.1:** 2 / 3

### 1.2 Operator e instalación (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Chart `open-telemetry/opentelemetry-operator` versión `0.74.x` (no `latest`) | 2 | 2 | 0.74.0 ✓ |
| cert-manager presente como prerequisito | 1 | 1 | 1.16.1 instalado en install.sh ✓ |
| Resources del operator dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 1 | 64-128Mi ✓ |
| `watchNamespace: ""` configurado (operator ve todos los namespaces) | 1 | 1 | Default all-namespaces ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Verificación de CRDs (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CRD `opentelemetrycollectors.opentelemetry.io` presente en el cluster | 1 | 1 | ✓ (evidencia en video) |
| Operator pod `Running` en `otel-operator-system` (evidencia en video) | 1 | 1 | hit2-debug-output.png ✓ |

**Subtotal 1.3:** 2 / 2

**TOTAL HIT #1:** 9 / 10

---

## HIT #2 — OpenTelemetryCollector en modo DaemonSet (15 puntos)

### 2.1 CR OpenTelemetryCollector (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Manifiesto `collector-agent.yaml` define CR `kind: OpenTelemetryCollector` (no Deployment directo) | 2 | 2 | ✓ |
| `mode: daemonset` configurado | 1 | 1 | ✓ |
| Imagen `otel/opentelemetry-collector-contrib:0.110.x` (no `core`, no `latest`) | 2 | 2 | 0.110.0 ✓ |
| Tolerations para nodo control-plane k3s (single-node) | 1 | 1 | ✓ |

**Subtotal 2.1:** 6 / 6

### 2.2 Pipeline receivers → processors → exporters (7 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Receiver `filelog` configurado leyendo `/var/log/pods/ml-scraper_*` | 2 | 2 | `/var/log/pods/ml-scraper_*/*/*.log` ✓ |
| Processor `batch` configurado | 1 | 1 | ✓ |
| Processor `k8sattributes` configurado para enriquecer con namespace, pod name, labels | 2 | 2 | Extracción comprehensiva de metadata k8s ✓ |
| Service pipeline conecta receivers → processors → exporters correctamente | 2 | 2 | filelog → batch → k8sattributes → [loki, elasticsearch] ✓ |

**Subtotal 2.2:** 7 / 7

### 2.3 RBAC (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| `rbac.yaml` con ServiceAccount + ClusterRole para que `k8sattributes` lea pods vía API k8s | 2 | 2 | 900 bytes con SA, ClusterRole, ClusterRoleBinding ✓ |

**Subtotal 2.3:** 2 / 2

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — Fan-out simultáneo a Loki + Elasticsearch (25 puntos)

### 3.1 Exporters configurados (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Exporter `otlphttp/loki` apuntando a `http://loki.observability.svc.cluster.local:3100` | 3 | 3 | `/otlp` endpoint ✓ |
| Exporter `elasticsearch` apuntando al cluster ECK con credenciales (secret copiado al namespace `otel`) | 3 | 3 | `https://scraper-es-http.elastic.svc.cluster.local:9200` ✓ |
| Secret de elastic copiado de `elastic` a `otel` en `install.sh` (no hardcodeado) | 2 | 2 | Script de copia automática de secret en install.sh ✓ |

**Subtotal 3.1:** 8 / 8

### 3.2 Verificación de fan-out (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper aparecen en Loki / Grafana Explore (evidencia en video/screenshot) | 4 | 4 | hit3-fanout-loki.png ✓ |
| Logs del scraper aparecen en Elasticsearch / Kibana Discover (evidencia en video/screenshot) | 4 | 4 | hit3-fanout-elastic.png ✓ |
| Mismo `log_id` (o campo único) identificable en ambos backends — matching demostrado | 4 | 4 | UUID generado por processor `transform`, visible en ambos backends ✓ |

**Subtotal 3.2:** 12 / 12

### 3.3 Screenshots de evidencia (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit3-fanout-loki.png` con el `log_id` visible | 2 | 2 | 226.2 KB ✓ |
| Existe `otel/screenshots/hit3-fanout-elastic.png` con el mismo `log_id` visible | 2 | 2 | 296.1 KB ✓ |
| Los dos screenshots corresponden al mismo evento (mismo timestamp razonable) | 1 | 1 | ✓ |

**Subtotal 3.3:** 5 / 5

**TOTAL HIT #3:** 25 / 25

---

## HIT #4 — Promtail + Fluent Bit escalados a 0 (15 puntos)

### 4.1 Escalado a 0 (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Promtail DaemonSet en namespace `observability` escalado a 0 | 3 | 3 | `_patch-promtail-zero.json` strategic merge patch ✓ |
| Fluent Bit DaemonSet en namespace `elastic` escalado a 0 | 3 | 2 | Escalado via install.sh (no hay patch file dedicado como para Promtail). Funciona pero menos declarativo. |

**Subtotal 4.1:** 5 / 6

### 4.2 Continuidad del flujo sin agentes legacy (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper siguen llegando a Loki después de bajar Promtail (evidencia) | 3 | 3 | hit4-old-agents-down.png ✓ |
| Logs del scraper siguen llegando a Elasticsearch después de bajar Fluent Bit (evidencia) | 3 | 3 | ✓ |

**Subtotal 4.2:** 6 / 6

### 4.3 Screenshot y documentación (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit4-old-agents-down.png` mostrando DaemonSets con 0 pods + logs llegando | 2 | 2 | 394.9 KB ✓ |
| `install.sh` incluye el escalado a 0 (no manual post-instalación) | 1 | 1 | ✓ |

**Subtotal 4.3:** 3 / 3

**TOTAL HIT #4:** 14 / 15

---

## HIT #5 — Scraper instrumentado con SDK Python (20 puntos)

> **NOTA:** El scraper en este repo es Java/Spring Boot, no Python. La implementación usa OTel Java SDK con Logback bridge. El directorio `otel/scraper-instrumentation/` no existe. Se evalúa lo que está presente.

### 5.1 Dependencias OTel (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/requirements-otel.txt` con versiones pinneadas `1.30.x` | 1 | 0 | Directorio `scraper-instrumentation/` **no existe**. Equivalente Java no está en otel/ |
| `opentelemetry-sdk==1.30.x`, `opentelemetry-exporter-otlp-proto-grpc==1.30.x` en `requirements.txt` del scraper | 2 | 0 | No verificable desde este repo |

**Subtotal 5.1:** 0 / 3

### 5.2 Módulo `otel_setup.py` (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/otel_setup.py` con `LoggerProvider` + `BatchLogRecordProcessor` + `OTLPLogExporter` | 3 | 0 | Archivo no existe |
| `TracerProvider` configurado | 2 | 0 | No verificable |
| Lee `OTEL_EXPORTER_OTLP_ENDPOINT` de env var (default `http://localhost:4317`) | 1 | 1 | `scraper-otlp-config.yaml` configura la variable ✓ |
| `Resource.create()` con `service.name`, `service.version` | 1 | 0 | No verificable |
| `atexit.register(logger_provider.shutdown)` o equivalente | 1 | 0 | No verificable |

**Subtotal 5.2:** 1 / 8

### 5.3 ConfigMap de endpoint + CronJob actualizado (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/manifests/scraper-otlp-config.yaml` ConfigMap con `OTEL_EXPORTER_OTLP_ENDPOINT` usando `NODE_IP` | 2 | 2 | 875 bytes ✓ |
| CronJob del scraper actualizado con `env.NODE_IP` via `fieldRef: status.hostIP` + `envFrom: configMapRef` | 2 | 2 | Configurado en scraper-otlp-config.yaml ✓ |
| Imagen del scraper re-publicada con tag diferenciado (ej: `scraper:otel-v1`) | 1 | 0 | No evidenciado en el repo |

**Subtotal 5.3:** 4 / 5

### 5.4 Verificación SDK (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Log records en Loki/Kibana tienen `trace_id` no vacío (evidencia en video — query LogQL o KQL) | 3 | 0 | Sin SDK Python/Java en otel/, no es verificable. Screenshots de Hit #3 muestran `log_id` (UUID generado por collector) pero no `trace_id` del SDK |
| Log records tienen `span_id` no vacío | 1 | 0 | Ídem |

**Subtotal 5.4:** 0 / 4

### Observaciones Hit #5
```
El directorio otel/scraper-instrumentation/ está ausente. El TP2/P3/README menciona
"Java/Spring Boot instrumentation using OTel SDK + Logback bridge" pero el código
de instrumentación no está en el repositorio otel/ ni se evidencia en screenshots.
El `log_id` visible en los screenshots de Hit #3 es un UUID generado por el processor
`transform` del collector (no un trace_id del SDK). Son cosas distintas.

Para aprobar este hit en una re-entrega: subir el módulo de setup OTel del scraper
(Python u otro lenguaje) con las dependencias pinneadas, y mostrar `trace_id` no vacío
en una query LogQL o KQL.
```

**TOTAL HIT #5:** 5 / 20

---

## ADR — `0010-instrumentacion-vendor-neutral.md` (15 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0010-instrumentacion-vendor-neutral.md` (numeración continua) | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| No es genérico / copiado de la consigna — refleja el razonamiento del equipo | 1 | 1 | 2,235 bytes, razonamiento propio ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona lock-in con Grafana Labs (Promtail) y Elastic (Fluent Bit → ES) como motivación | 3 | 2 | Menciona "dual-stack logging scenario" y "vendor decoupling" pero no nombra explícitamente el lock-in de Grafana Labs y Elastic por separado |
| Menciona costo operativo de mantener 2 agentes por nodo vs 1 colector OTel | 3 | 1 | "operational overhead reduction" sin cuantificar (RAM, CPU, complejidad operativa) |
| Menciona adopción de OTLP por los 4 grandes SaaS (Datadog, New Relic, Dynatrace, Splunk) | 3 | 0 | **Ausente**. No nombra a ninguno de los 4 vendors que adoptaron OTLP como protocolo nativo |
| Menciona la inversión de re-instrumentar el scraper y por qué paga a mediano plazo | 2 | 0 | **Ausente**. No analiza el ROI de la re-instrumentación |
| Remite al ADR comparativo de Parte 4 para la decisión final | 1 | 0 | No hay referencia explícita a la Parte 4 |

**Subtotal 6.2:** 3 / 12

### Observaciones ADR
```
El ADR 0010 tiene la estructura correcta pero le falta el argumento técnico central:
por qué OTLP/OTel es superior a seguir con Promtail+Fluent Bit. Específicamente:

1. Los 4 vendors que adoptaron OTLP (Datadog, New Relic, Dynatrace, Splunk) son
   el argumento más fuerte para OTel — si todos los SaaS hablan OTLP, el switch
   de backend es solo cambiar una línea de YAML en el collector.

2. El costo operativo debería cuantificarse: 2 DaemonSets (Promtail + Fluent Bit)
   vs 1 OTel Collector (reducción de ~90-130Mi RAM por nodo).

3. La re-instrumentación del scraper (que se necesita para trace_id) es una inversión
   que paga cuando el equipo crece y necesita tracing distribuido.

Este ADR va a ser preguntado en la defensa de Parte 4. Recomendamos reforzarlo.
```

**TOTAL ADR:** 6 / 15

---

## BONUS — Hit #6: Traces visibles en Jaeger (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Backend de traces desplegado: Jaeger `jaegertracing/jaeger` v`3.4.x` (o Grafana Tempo) en namespace `otel` | 1 | 0 | No hay Jaeger ni Tempo en el repo |
| Exporter OTLP/traces en el collector apuntando al backend | 1 | 0 | No hay exporter de traces |
| Spans del scraper visibles en la UI de Jaeger/Tempo — screenshot `hit5-otlp-trace.png` | 2 | 0 | No hay screenshot |
| Existe ADR `0011-traces-vs-solo-logs.md` justificando por qué traces además de logs | 1 | 0 | ADR 0011 no existe |

**TOTAL BONUS Hit #6:** 0 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 3

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — OTel Operator + CRDs | 10% | 9 | 10 |
| Hit #2 — Collector DaemonSet + pipeline + k8sattributes | 15% | 15 | 15 |
| Hit #3 — Fan-out Loki + ES con log_id matching ⭐ | 25% | 25 | 25 |
| Hit #4 — Promtail + Fluent Bit a 0, flujo intacto | 15% | 14 | 15 |
| Hit #5 — SDK Python, trace_id populado | 20% | 5 | 20 |
| ADR `0010-instrumentacion-vendor-neutral.md` | 15% | 6 | 15 |
| **TOTAL** | **100%** | **74** | **100** |
| Bonus Hit #6 — Traces en Jaeger + ADR 0011 | +5% | 0 | +5 |

### Nota Final TP2 Parte 3: 7.4 / 10

---

## Devolución General

**Fortalezas:**
```
Hit #3 (fan-out) perfecto: mismo log_id matching en Loki y Elasticsearch, screenshots
claros, secret copiado automáticamente entre namespaces. La parte más difícil del TP
está muy bien resuelta.
Collector bien diseñado: contrib, DaemonSet, k8sattributes, RBAC, tolerations.
```

**Puntos a mejorar:**
```
Hit #5 (SDK): es el gap más grande (15 pts perdidos). Falta el directorio
scraper-instrumentation/ con el código de setup OTel del scraper y evidencia
de trace_id/span_id no vacíos en los logs.

ADR 0010: le faltan los argumentos técnicos clave:
  - Nominar los 4 vendors que adoptaron OTLP (Datadog, New Relic, Dynatrace, Splunk)
  - Cuantificar el costo operativo de 2 DaemonSets vs 1
  - Mencionar el ROI de re-instrumentar
```

**Comentarios para el grupo:**
```
La infraestructura del collector es excelente. El punto débil es la capa de aplicación
(SDK del scraper) que es el argumento principal de OTel sobre Promtail+Fluent Bit:
sin trace_id propagado desde el código, el OTel Collector se comporta igual que Fluent Bit
pero más complejo. Para la defensa de Parte 4, van a necesitar explicar esta distinción.

Si pueden agregar el scraper-instrumentation/ con trace_id antes de la defensa,
la nota sube significativamente.
```
