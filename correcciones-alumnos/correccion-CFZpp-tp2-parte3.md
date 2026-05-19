# Corrección TP2 — Parte 3: OpenTelemetry Collector + SDK + multi-backend

**Grupo:** CFZ++
**Integrantes:**
- Contardi, Gustavo
- _______________________________________________
- _______________________________________________
- _______________________________________________
- _______________________________________________
**Repo GitHub:** https://github.com/GustavoContardi/TP1-Selenium (TP2 en subcarpeta `/TP2/`)
**Video (YouTube):** _______________________________________________
**Fecha de entrega:** _______________________________________________
**Fecha de corrección:** 2026-05-09
**Corrector:** M. Rapaport

---

## ⛔ VERIFICACIÓN BLOQUEANTE PREVIA

| # | Verificación | Estado | Notas |
|---|-------------|--------|-------|
| B1 | TP2 · Parte 1 entregada y aprobada (≥ 60/100) — Loki corriendo en `observability` | ✅ OK | P1: 7.9/10 |
| B2 | TP2 · Parte 2 entregada y aprobada (≥ 60/100) — EFK corriendo en `elastic` | ✅ OK | P2: 8.6/10 |
| B3 | Existe `otel/install.sh` ejecutable (carpeta separada de `observability/` y `efk/`) | ⛔ **FALLA** | **El directorio `TP2/otel/` no existe en el repositorio** |
| B4 | `otel/install.sh` funciona sobre cluster con Loki + EFK preexistentes | ⛔ **FALLA** | No aplica (directorio inexistente) |
| B5 | Helm charts pinneados a versiones específicas (no `latest`) | ⛔ **FALLA** | No aplica |
| B6 | Usa distribución `contrib` del collector (`otel/opentelemetry-collector-contrib`) — NO `core` | ⛔ **FALLA** | No aplica |
| B7 | `gitleaks detect` da 0 leaks (sin endpoints con basic-auth embebido ni secrets) | ⛔ **FALLA** | No aplica |
| B8 | Auto-verificación de 8 ítems ejecutada antes del push final | ⛔ **FALLA** | No aplica |

**¿Pasa verificación bloqueante?** ⛔ **NO** — nota = **0**, fin de corrección

---

## CORRECCIÓN DETENIDA POR BLOQUEANTE B3

El directorio `TP2/otel/` no existe en el repositorio. La Parte 3 (OpenTelemetry) no fue iniciada.

Confirmado: los siguientes archivos retornan 404:
- `TP2/otel/install.sh`
- `TP2/otel/helm/otel-operator-values.yaml`
- `TP2/otel/manifests/collector-agent.yaml`
- `TP2/otel/scraper-instrumentation/otel_setup.py`
- `TP2/otel/scraper-instrumentation/requirements-otel.txt`

Adicionalmente, el ADR `0010-instrumentacion-vendor-neutral.md` no existe (afectará también la Parte 4).

---

## NOTA FINAL TP2 PARTE 3: **0 / 10**

---

## Devolución General

**Lo que hay que entregar para esta parte:**

```
1. otel/install.sh
   — Instala OTel Operator via chart open-telemetry/opentelemetry-operator 0.74.x
   — Requiere cert-manager como prerequisito (ya instalado en Parte 2)
   — Despliega el CR OpenTelemetryCollector en modo DaemonSet
   — Escala Promtail y Fluent Bit a 0 réplicas
   — Copia el secret de elastic del namespace elastic al namespace otel

2. otel/helm/otel-operator-values.yaml
   — watchNamespace: ""
   — resources: requests ≤ 64Mi / limits ≤ 128Mi

3. otel/manifests/collector-agent.yaml
   — kind: OpenTelemetryCollector, mode: daemonset
   — imagen: otel/opentelemetry-collector-contrib:0.110.x (NO core, NO latest)
   — Pipeline: filelog receiver → k8sattributes + batch processors → [otlphttp/loki, elasticsearch] exporters
   — Tolerations para nodo control-plane k3s

4. otel/manifests/rbac.yaml
   — ServiceAccount + ClusterRole para que k8sattributes lea pods via API k8s

5. otel/scraper-instrumentation/otel_setup.py
   — LoggerProvider + BatchLogRecordProcessor + OTLPLogExporter
   — TracerProvider configurado
   — Lee OTEL_EXPORTER_OTLP_ENDPOINT de env var
   — Resource.create() con service.name, service.version
   — atexit.register(logger_provider.shutdown)

6. otel/scraper-instrumentation/requirements-otel.txt
   — opentelemetry-sdk==1.30.x
   — opentelemetry-exporter-otlp-proto-grpc==1.30.x

7. otel/manifests/scraper-otlp-config.yaml
   — ConfigMap con OTEL_EXPORTER_OTLP_ENDPOINT usando NODE_IP
   — CronJob actualizado con fieldRef: status.hostIP

8. docs/adr/0010-instrumentacion-vendor-neutral.md
   — Mencionar: lock-in Grafana Labs + Elastic, costo 2 agentes vs 1,
     adopción OTLP por Datadog/New Relic/Dynatrace/Splunk, ROI re-instrumentar
```

**Contexto para el grupo:**
```
Las Partes 1 y 2 son sólidas (P1: 7.9, P2: 8.6). La Parte 3 no fue iniciada.
La implementación sigue un patrón bien definido:

La misma imagen contrib ya usada en otros proyectos del curso. La configuración del
collector-agent.yaml es la pieza más importante: el pipeline filelog → k8sattributes
→ batch → [loki, elasticsearch] es el corazón del TP.

Para el SDK Python: el scraper ya tiene logging_setup.py. La instrumentación OTel
agrega otel_setup.py encima: mismo patrón, mismos campos, pero los logs van via
OTLP/gRPC al collector en lugar de a stdout para Promtail.

El fan-out (misma línea de log en Loki Y en Kibana con el mismo log_id) es la
evidencia que vale 25 de los 100 puntos de esta parte.

Si entregan antes de la fecha de defensa, se reabre la corrección.
```
