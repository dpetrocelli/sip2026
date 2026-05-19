# Corrección TP2 — Parte 3: OpenTelemetry Collector + SDK + multi-backend

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
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) — Loki corriendo en `observability` | ✅ OK | P1: 8.1/10 |
| B2 | TP2 · Parte 2 entregada y aprobada (≥ 60/100) — EFK corriendo en `elastic` | ✅ OK | P2: 8.0/10 |
| B3 | Existe `otel/install.sh` ejecutable (carpeta separada de `observability/` y `efk/`) | ✅ OK | ✓ |
| B4 | `otel/install.sh` funciona sobre cluster con Loki + EFK preexistentes | ✅ OK | ✓ |
| B5 | Helm charts pinneados a versiones específicas (no `latest`) | ✅ OK | ✓ |
| B6 | Usa distribución `contrib` del collector (`otel/opentelemetry-collector-contrib`) — NO `core` | ✅ OK | `otel/opentelemetry-collector-contrib:0.110.0` ✓ |
| B7 | `gitleaks detect` da 0 leaks (sin endpoints con basic-auth embebido ni secrets) | ✅ OK | ✓ |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | ✓ |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

---

## HIT #1 — Deploy del OpenTelemetry Operator (10 puntos)

### 1.1 Estructura del repositorio (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe carpeta `otel/` con `README.md`, `helm/`, `manifests/`, `scraper-instrumentation/`, `install.sh` | 1 | 1 | ✓ |
| Existe `otel/helm/otel-operator-values.yaml` con resources definidos | 1 | 1 | ✓ |
| Existe `otel/manifests/namespace.yaml`, `collector-agent.yaml`, `rbac.yaml`, `scraper-otlp-config.yaml` | 1 | 1 | ✓ |

**Subtotal 1.1:** 3 / 3

### 1.2 Operator e instalación (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Chart `open-telemetry/opentelemetry-operator` versión `0.74.x` (no `latest`) | 2 | 2 | 0.74.0 ✓ |
| cert-manager presente como prerequisito (heredado de Parte 2 o instalado en `install.sh`) | 1 | 1 | Heredado de cert-manager instalado en P2 ✓ |
| Resources del operator dentro de límites: requests ≤ 64Mi / limits ≤ 128Mi | 1 | 1 | ✓ |
| `watchNamespace: ""` configurado (operator ve todos los namespaces) | 1 | 1 | ✓ |

**Subtotal 1.2:** 5 / 5

### 1.3 Verificación de CRDs (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| CRD `opentelemetrycollectors.opentelemetry.io` presente en el cluster | 1 | 1 | ✓ |
| Operator pod `Running` en `otel-operator-system` (evidencia en video) | 1 | 1 | ✓ |

**Subtotal 1.3:** 2 / 2

### Observaciones Hit #1
```
Operator bien configurado. Versión correcta, watchNamespace vacío, cert-manager
heredado de P2. Sin observaciones.
```

**TOTAL HIT #1:** 10 / 10

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
| Receiver `filelog` configurado leyendo `/var/log/pods/ml-scraper_*` | 2 | 2 | ✓ |
| Processor `batch` configurado | 1 | 1 | ✓ |
| Processor `k8sattributes` configurado para enriquecer con namespace, pod name, labels | 2 | 2 | ✓ |
| Service pipeline conecta receivers → processors → exporters correctamente | 2 | 2 | ✓ |

**Subtotal 2.2:** 7 / 7

### 2.3 RBAC (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| `rbac.yaml` con ServiceAccount + ClusterRole para que `k8sattributes` lea pods vía API k8s | 2 | 2 | ✓ |

**Subtotal 2.3:** 2 / 2

### Observaciones Hit #2
```
Pipeline completo y correcto. Distribución contrib con filelog → k8sattributes → batch
bien encadenados. RBAC correcto para que k8sattributes tenga acceso a la API de k8s.
```

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — Fan-out simultáneo a Loki + Elasticsearch (25 puntos)

### 3.1 Exporters configurados (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Exporter `otlphttp/loki` apuntando a `http://loki.observability.svc.cluster.local:3100` | 3 | 3 | ✓ |
| Exporter `elasticsearch` apuntando al cluster ECK con credenciales (secret copiado al namespace `otel`) | 3 | 3 | Secret copiado de `elastic` a `otel` en install.sh ✓ |
| Secret de elastic copiado de `elastic` a `otel` en `install.sh` (no hardcodeado) | 2 | 2 | `kubectl get secret ... -n elastic -o yaml \| kubectl apply -n otel` ✓ |

**Subtotal 3.1:** 8 / 8

### 3.2 Verificación de fan-out (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper aparecen en Loki / Grafana Explore (evidencia en video/screenshot) | 4 | 4 | Screenshot `hit3-fanout-loki.png` con log_id visible ✓ |
| Logs del scraper aparecen en Elasticsearch / Kibana Discover (evidencia en video/screenshot) | 4 | 4 | Screenshot `hit3-fanout-elastic.png` ✓ |
| Mismo `log_id` (o campo único) identificable en ambos backends — matching demostrado | 4 | 4 | Mismo `log_id` visible en ambos screenshots con mismo timestamp ✓ |

**Subtotal 3.2:** 12 / 12

### 3.3 Screenshots de evidencia (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit3-fanout-loki.png` con el `log_id` visible | 2 | 2 | ✓ |
| Existe `otel/screenshots/hit3-fanout-elastic.png` con el mismo `log_id` visible | 2 | 2 | ✓ |
| Los dos screenshots corresponden al mismo evento (mismo timestamp razonable) | 1 | 1 | ✓ |

**Subtotal 3.3:** 5 / 5

### Observaciones Hit #3
```
Fan-out perfectamente demostrado. Screenshots con log_id coincidente en ambos backends,
mismo timestamp. El secret de Elasticsearch bien copiado al namespace otel sin hardcodear.
```

**TOTAL HIT #3:** 25 / 25

---

## HIT #4 — Promtail + Fluent Bit escalados a 0 (15 puntos)

### 4.1 Escalado a 0 (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Promtail DaemonSet en namespace `observability` escalado a 0 (`replicas: 0` o `kubectl scale`) | 3 | 3 | `kubectl scale daemonset promtail -n observability --replicas=0` en install.sh ✓ |
| Fluent Bit DaemonSet en namespace `elastic` escalado a 0 | 3 | 3 | ✓ |

**Subtotal 4.1:** 6 / 6

### 4.2 Continuidad del flujo sin agentes legacy (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper siguen llegando a Loki después de bajar Promtail (evidencia) | 3 | 3 | Screenshot `hit4-old-agents-down.png` muestra DaemonSets en 0 + logs en Grafana ✓ |
| Logs del scraper siguen llegando a Elasticsearch después de bajar Fluent Bit (evidencia) | 3 | 3 | ✓ |

**Subtotal 4.2:** 6 / 6

### 4.3 Screenshot y documentación (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/screenshots/hit4-old-agents-down.png` mostrando DaemonSets con 0 pods + logs llegando | 2 | 2 | ✓ |
| `install.sh` incluye el escalado a 0 (no manual post-instalación) | 1 | 1 | ✓ |

**Subtotal 4.3:** 3 / 3

### Observaciones Hit #4
```
Escalado a 0 incluido en install.sh. Continuidad del flujo bien evidenciada. Hit completo.
```

**TOTAL HIT #4:** 15 / 15

---

## HIT #5 — Scraper instrumentado con SDK Python (20 puntos)

### 5.1 Dependencias OTel (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/requirements-otel.txt` con versiones pinneadas `1.30.x` | 1 | 1 | `opentelemetry-sdk==1.30.0` ✓ |
| `opentelemetry-sdk==1.30.x`, `opentelemetry-exporter-otlp-proto-grpc==1.30.x` en `requirements.txt` del scraper | 2 | 2 | ✓ |

**Subtotal 5.1:** 3 / 3

### 5.2 Módulo `otel_setup.py` (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/scraper-instrumentation/otel_setup.py` con `LoggerProvider` + `BatchLogRecordProcessor` + `OTLPLogExporter` | 3 | 3 | ✓ |
| `TracerProvider` configurado (base para hit #6 bonus y correlación) | 2 | 2 | ✓ |
| Lee `OTEL_EXPORTER_OTLP_ENDPOINT` de env var (default `http://localhost:4317`) | 1 | 1 | ✓ |
| `Resource.create()` con `service.name`, `service.version` | 1 | 1 | ✓ |
| `atexit.register(logger_provider.shutdown)` o equivalente (evita pérdida de logs en buffer) | 1 | 1 | ✓ |

**Subtotal 5.2:** 8 / 8

### 5.3 ConfigMap de endpoint + CronJob actualizado (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `otel/manifests/scraper-otlp-config.yaml` ConfigMap con `OTEL_EXPORTER_OTLP_ENDPOINT` usando `NODE_IP` | 2 | 2 | ✓ |
| CronJob del scraper actualizado con `env.NODE_IP` via `fieldRef: status.hostIP` + `envFrom: configMapRef` | 2 | 2 | ✓ |
| Imagen del scraper re-publicada con tag diferenciado (ej: `scraper:otel-v1`) | 1 | 1 | `scraper:otel-v1` ✓ |

**Subtotal 5.3:** 5 / 5

### 5.4 Verificación SDK (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Log records en Loki/Kibana tienen `trace_id` no vacío (evidencia en video — query LogQL o KQL) | 3 | 3 | `trace_id` visible en ambos backends ✓ |
| Log records tienen `span_id` no vacío | 1 | 0 | `span_id` no aparece en los screenshots de evidencia. `trace_id` sí. |

**Subtotal 5.4:** 3 / 4

### Observaciones Hit #5
```
SDK Python implementado correctamente — otel_setup.py con LoggerProvider completo,
requirements-otel.txt con versiones 1.30.0 pinneadas, ConfigMap + CronJob actualizados.
trace_id poblado desde el SDK visible en ambos backends. El único gap: span_id no
aparece en la evidencia. El TracerProvider está configurado por lo que span_id debería
estar presente — faltaría un screenshot de Kibana con el campo span_id visible.
```

**TOTAL HIT #5:** 19 / 20

---

## ADR — `0010-instrumentacion-vendor-neutral.md` (15 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0010-instrumentacion-vendor-neutral.md` (numeración continua) | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| No es genérico / copiado de la consigna — refleja el razonamiento del equipo | 1 | 1 | ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido (12 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona lock-in con Grafana Labs (Promtail) y Elastic (Fluent Bit → ES) como motivación | 3 | 3 | ✓ |
| Menciona costo operativo de mantener 2 agentes por nodo vs 1 colector OTel | 3 | 3 | ✓ |
| Menciona adopción de OTLP por los 4 grandes SaaS (Datadog, New Relic, Dynatrace, Splunk) | 3 | 0 | No aparece. El ADR menciona OTel como "estándar CNCF" pero no nombra los 4 vendors SaaS que adoptaron OTLP. Esto es lo que convierte la afirmación en argumento. |
| Menciona la inversión de re-instrumentar el scraper y por qué paga a mediano plazo | 2 | 2 | ✓ |
| Remite al ADR comparativo de Parte 4 para la decisión final | 1 | 0 | No hay referencia a la Parte 4 ni al ADR 0012. |

**Subtotal 6.2:** 8 / 12

### Observaciones ADR
```
ADR 0010 cubre lock-in y costo de 2 agentes bien. Dos gaps:
1. Los 4 vendors SaaS (Datadog, New Relic, Dynatrace, Splunk) que adoptaron OTLP nativamente
   son el argumento concreto de que la apuesta CNCF es ganadora. Sin nombrarlos, el
   argumento queda abstracto.
2. Sin referencia al ADR 0012 (Parte 4) queda como decisión final en lugar de intermedia.
   Agregar: "La selección definitiva entre stacks se documenta en ADR 0012."
```

**TOTAL ADR:** 11 / 15

---

## BONUS — Hit #6: Traces visibles en Jaeger (+5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Backend de traces desplegado: Jaeger `jaegertracing/jaeger` v`3.4.x` (o Grafana Tempo) en namespace `otel` | 1 | 0 | No implementado |
| Exporter OTLP/traces en el collector apuntando al backend | 1 | 0 | No implementado |
| Spans del scraper visibles en la UI de Jaeger/Tempo — screenshot `hit5-otlp-trace.png` | 2 | 0 | No implementado |
| Existe ADR `0011-traces-vs-solo-logs.md` justificando por qué traces además de logs | 1 | 0 | No implementado |

**TOTAL BONUS Hit #6:** 0 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 3

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — OTel Operator + CRDs | 10% | 10 | 10 |
| Hit #2 — Collector DaemonSet + pipeline + k8sattributes | 15% | 15 | 15 |
| Hit #3 — Fan-out Loki + ES con log_id matching ⭐ | 25% | 25 | 25 |
| Hit #4 — Promtail + Fluent Bit a 0, flujo intacto | 15% | 15 | 15 |
| Hit #5 — SDK Python, trace_id populado | 20% | 19 | 20 |
| ADR `0010-instrumentacion-vendor-neutral.md` | 15% | 11 | 15 |
| **TOTAL** | **100%** | **95** | **100** |
| Bonus Hit #6 — Traces en Jaeger + ADR 0011 | +5% | 0 | +5 |

### Nota Final TP2 Parte 3: **9.5 / 10**

---

## Devolución General

**Fortalezas:**
```
Fan-out Loki + ES completamente demostrado con log_id matching en ambos backends.
Python SDK correctamente implementado: LoggerProvider + BatchLogRecordProcessor +
OTLPLogExporter + TracerProvider + atexit shutdown. requirements-otel.txt con 1.30.0.
ConfigMap + fieldRef: status.hostIP bien resuelto para el endpoint del collector.
Escalado a 0 incluido en install.sh con continuidad de flujo evidenciada.
```

**Puntos a mejorar:**
```
ADR 0010 (−4 pts): Agregar los 4 vendors que adoptaron OTLP (Datadog, New Relic,
Dynatrace, Splunk) — convierte "estándar CNCF" en argumento concreto de mercado.
Agregar referencia al ADR 0012 como punto de convergencia.

Hit #5 span_id (−1 pt): El TracerProvider está configurado. Solo falta un screenshot
en Kibana con el campo span_id visible en un log record. Tarda 2 minutos.
```

**Comentarios para el grupo:**
```
La Parte 3 es técnicamente excelente — el fan-out con log_id matching y el SDK Python
completo son las piezas más difíciles del TP. Los −5 pts son de documentación
(ADR 0010 incompleto) y de un screenshot faltante (span_id). La implementación
subyacente está correcta. Con el ADR 0010 ampliado, esta parte sería un 9.9.
```
