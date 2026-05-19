# Corrección TP2 — Parte 1: Logging centralizado con Loki + Promtail + Grafana

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
| B1 | TP1 · Parte 2 entregado y aprobado (mínimo 60/100) | ✅ OK | |
| B2 | Existe `observability/install.sh` ejecutable | ✅ OK | |
| B3 | `install.sh` levanta el stack completo en cluster limpio (un solo comando) | ✅ OK | `set -euo pipefail`, idempotente con `--dry-run=client \| kubectl apply` |
| B4 | Helm charts con versiones específicas — NO usa `loki-stack` chart | ✅ OK | Loki 6.16.0, Promtail 6.16.0, Grafana 8.5.0 |
| B5 | `gitleaks detect` da 0 leaks (sin secrets commiteados) | ✅ OK | CI con gitleaks-action v2; .gitignore excluye .env |
| B6 | Auto-verificación de 8 ítems ejecutada antes del push final | ✅ OK | README.md documenta el checklist; CI corre Kubernetes dry-run |

**¿Pasa verificación bloqueante?** ✅ SÍ — continuar

---

## HIT #1 — Deploy del stack Loki + Promtail + Grafana (20 puntos)

### 1.1 Estructura del repositorio (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe carpeta `observability/` con README.md | 1 | 1 | 969 palabras ✓ |
| Existen `helm/loki-values.yaml`, `helm/promtail-values.yaml`, `helm/grafana-values.yaml` | 1 | 1 | ✓ |
| Existen `manifests/namespace.yaml` y `manifests/grafana-secret.yaml` (con placeholder, no real) | 1 | 0 | `manifests/` tiene namespace.yaml, alert-rules.yaml, contact-point.yaml, notification-policy.yaml, grafana-nodeport.yaml. **`grafana-secret.yaml` como archivo placeholder no está**. El secret se crea en install.sh desde env var (correcto) pero no hay template commiteado. |
| Existe `observability/install.sh` idempotente con todos los pasos | 1 | 1 | ✓ |

**Subtotal 1.1:** 3 / 4

### 1.2 Charts y versiones (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Loki chart `grafana/loki` en versión `6.16.x` (no `latest`) | 1 | 1 | 6.16.0 ✓ |
| Promtail chart `grafana/promtail` en versión `6.16.x` o Alloy `0.9.x` | 1 | 1 | 6.16.0 ✓ |
| Grafana chart `grafana/grafana` en versión `8.5.x` | 1 | 1 | 8.5.0 ✓ |
| NO usa `grafana/loki-stack` (chart deprecado) | 1 | 1 | Correcto ✓ |

**Subtotal 1.2:** 4 / 4

### 1.3 Configuración de Loki (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Modo `SingleBinary` (no simple-scalable ni microservices) | 1 | 1 | ✓ |
| Storage type `filesystem` + PVC `local-path` 5 Gi | 1 | 1 | ✓ |
| Resources dentro de límites: requests ≤ 256 Mi / limits ≤ 512 Mi | 1 | 1 | 256Mi req / 512Mi limit ✓ |
| Retención configurada: `retention_period: 168h` (7 días) | 1 | 1 | **168h configurado correctamente** ✓ |
| `read`, `write`, `backend` con replicas: 0 (desactivados para single-binary) | 1 | 1 | ✓ |

**Subtotal 1.3:** 5 / 5

### 1.4 Grafana y datasource (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Admin password manejada vía Secret (no commiteada en values.yaml) | 2 | 2 | Referencias secret `grafana-admin` con keys admin-user/admin-password ✓ |
| `install.sh` crea el secret leyendo de `$GRAFANA_ADMIN_PASSWORD` env var | 1 | 1 | `: "${GRAFANA_ADMIN_PASSWORD:?Set GRAFANA_ADMIN_PASSWORD before running}"` ✓ |
| Datasource Loki provisionado as-code en `grafana-values.yaml` (no manual en UI) | 1 | 1 | `http://loki.observability.svc.cluster.local:3100`, uid: loki, default: true ✓ |
| Grafana accesible en NodePort 30000 (o ingress equivalente) | 1 | 1 | NodePort 30000 ✓ |

**Subtotal 1.4:** 5 / 5

### 1.5 Verificación de funcionamiento (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Los 3 pods + DaemonSet están `Running` tras ejecutar `install.sh` | 1 | 1 | hit1.png ✓ |
| Datasource Loki validado en Grafana (status 200 — evidencia en video/screenshot) | 1 | 1 | ✓ |

**Subtotal 1.5:** 2 / 2

### Observaciones Hit #1
```
Excelente configuración. Retención 168h correcta (a diferencia de otros grupos).
El único detalle menor: no hay manifests/grafana-secret.yaml como archivo placeholder
commiteado — está bien que el secret se cree dinámicamente desde env var, pero tener
un template con el campo vacío sirve como documentación de la estructura esperada.
```

**TOTAL HIT #1:** 19 / 20

---

## HIT #2 — Recolección de logs del scraper con labels Kubernetes (15 puntos)

### 2.1 Configuración de Promtail/Alloy (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| DaemonSet corriendo con tolerations para nodo control-plane k3s (single-node) | 2 | 2 | `operator: Exists` NoSchedule ✓ |
| Configuración de `clients` apunta a `loki.observability.svc.cluster.local:3100` | 2 | 2 | `/loki/api/v1/push` ✓ |
| Resources dentro de límites (Promtail: requests ≤ 64 Mi / limits ≤ 128 Mi) | 1 | 1 | 64Mi req / 128Mi limit ✓ |
| Pipeline stages configurados (no solo config default) | 1 | 1 | kubernetes_sd_configs + relabel_configs ✓ |

**Subtotal 2.1:** 6 / 6

### 2.2 Labels Kubernetes útiles (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Label `namespace` presente en los streams de Loki | 2 | 2 | ✓ |
| Label `pod` o `app` presente | 1 | 1 | pod, container, app, node ✓ |
| Label `job_name` (o equivalente para CronJob) presente | 2 | 2 | job_name mapeado ✓ |
| Labels NO producen cardinality explosion (sin labels de alta cardinalidad como UUID) | 1 | 1 | Filtro `app=scraper` + relabeling controlado ✓ |

**Subtotal 2.2:** 6 / 6

### 2.3 Evidencia de recolección (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Logs del scraper visibles en Grafana Explore / Loki | 2 | 2 | hit2-labels.png ✓ |
| Query básica `{namespace="ml-scraper"}` retorna resultados (evidencia en video) | 1 | 1 | ✓ |

**Subtotal 2.3:** 3 / 3

**TOTAL HIT #2:** 15 / 15

---

## HIT #3 — Migrar el scraper a logs JSON estructurados (20 puntos)

### 3.1 Implementación de logs JSON (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Usa `python-json-logger` (o equivalente) — no solo `json.dumps()` manual | 2 | 2 | Scraper Node.js usa Winston con JSON output; aceptado como equivalente ✓ |
| Cada línea de log es un JSON válido (line-delimited, no pretty-print) | 2 | 2 | logLineJSON.png confirma JSON estructurado ✓ |
| Campo `level` presente (INFO/WARNING/ERROR) | 1 | 1 | ✓ |
| Campo `message` presente | 1 | 1 | ✓ |
| Campos de contexto del negocio presentes: `producto`, `browser`, o similares | 2 | 2 | Campos de negocio en log records ✓ |

**Subtotal 3.1:** 8 / 8

### 3.2 Compatibilidad con LogQL `| json` (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Campos son extraíbles via `| json` sin errores en Grafana | 3 | 3 | ejemploQ1.png, ejemploQ2.png ✓ |
| Query de ejemplo: `{namespace="ml-scraper"} \| json \| level="ERROR"` funciona | 2 | 2 | ✓ |
| No hay campos con nombres reservados o conflictivos en LogQL | 1 | 1 | ✓ |

**Subtotal 3.2:** 6 / 6

### 3.3 Calidad de la migración (6 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| No regresión: el scraper sigue funcionando correctamente (extrae datos) | 2 | 2 | logLinePlainText.png muestra before/after ✓ |
| `logging_setup.py` (o módulo equivalente) centraliza la configuración del logger JSON | 2 | 2 | Módulo equivalente Node.js con Winston ✓ |
| Niveles INFO/WARNING/ERROR usados semánticamente correctos | 2 | 2 | ✓ |

**Subtotal 3.3:** 6 / 6

**TOTAL HIT #3:** 20 / 20

---

## HIT #4 — LogQL cookbook: 5+ queries útiles (15 puntos)

### 4.1 Archivo y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `observability/queries/logql-cookbook.md` | 1 | 1 | ✓ |
| Cada query documenta: pregunta de negocio + query LogQL + explicación | 1 | 1 | ✓ |
| Al menos 5 queries (se acreditan hasta 7) | 1 | 1 | 5+ queries (Q1-Q5 + bonus) ✓ |

**Subtotal 4.1:** 3 / 3

### 4.2 Calidad y variedad de queries (10 pts)

| Query | Presente | Funciona en Grafana | Pts |
|-------|----------|---------------------|-----|
| Filtrar logs por nivel ERROR del scraper | ✅ | ✅ | 2 |
| Filtrar logs de un producto específico (`| json | producto="..."`) | ✅ | ✅ | 2 |
| Rate de logs por nivel en los últimos N minutos (`rate(...)`) | ✅ | ✅ | 2 |
| Contar errores por ejecución de CronJob | ✅ | ✅ | 2 |
| Query libre adicional relevante (1+ queries extra) | ✅ | ✅ | 2 |

**Subtotal 4.2:** 10 / 10

### 4.3 Evidencia de ejecución (2 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Las queries corren sin error en Grafana (evidencia en video/screenshots) | 2 | 2 | ejemploQ1.png, ejemploQ2.png ✓ |

**Subtotal 4.3:** 2 / 2

**TOTAL HIT #4:** 15 / 15

---

## HIT #5 — Dashboard Grafana provisionado as-code (20 puntos)

### 5.1 Provisioning as-code (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Existe `observability/dashboards/scraper-overview.json` | 2 | 2 | 12.3 KB ✓ |
| Dashboard configurado en `grafana-values.yaml` via `dashboardProviders` + `dashboardsConfigMaps` | 3 | 3 | File-based provisioning, 4 ConfigMap mounts, folder "SIP 2026" ✓ |
| El dashboard aparece automáticamente en Grafana tras `install.sh` (sin importar manualmente) | 3 | 3 | ✓ |

**Subtotal 5.1:** 8 / 8

### 5.2 Contenido del dashboard (8 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Panel de log rate por nivel (o similar) | 2 | 2 | ✓ |
| Panel de logs en tiempo real (log panel) | 2 | 2 | ✓ |
| Panel o stat de tasa de errores | 2 | 2 | ✓ |
| Al menos 3 panels con datos reales del scraper (evidencia en video) | 2 | 2 | hit5-dashboard.png ✓ |

**Subtotal 5.2:** 8 / 8

### 5.3 Calidad del JSON (4 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| JSON válido (parseable sin errores) | 1 | 1 | ✓ |
| `uid` único y consistente (no conflicto con otros dashboards) | 1 | 1 | ✓ |
| Variables de template (time range, namespace) configuradas | 2 | 2 | ✓ |

**Subtotal 5.3:** 4 / 4

**TOTAL HIT #5:** 20 / 20

---

## ADR — `0007-stack-de-logging.md` (10 puntos)

### 6.1 Estructura y formato (3 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Archivo en `docs/adr/0007-stack-de-logging.md` | 1 | 1 | ✓ |
| Secciones presentes: Contexto, Decisión, Consecuencias | 1 | 1 | ✓ |
| Continúa numeración de ADRs del TP1 · Parte 2 | 1 | 1 | 0001-0004 de TP1, 0007 continúa ✓ |

**Subtotal 6.1:** 3 / 3

### 6.2 Contenido de la decisión (5 pts)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Menciona requerimiento de retención (7 días) como constraint | 1 | 1 | ✓ |
| Menciona recursos del cluster (single-node k3s, ~6 GB RAM) | 1 | 1 | ✓ |
| Menciona alternativas descartadas: mínimo 4 (ELK, Datadog, Splunk, + 1 más) | 2 | 2 | 8 alternativas comparadas en tabla ✓ |
| Razonamiento real y específico del equipo (no genérico/copiado) | 1 | 1 | Referencias a design docs y best practices propias ✓ |

**Subtotal 6.2:** 5 / 5

**TOTAL ADR:** 8 / 10

---

## BONUS — Hit #6: Alertas (+ 5 puntos)

| Criterio | Pts | Obtenido | Notas |
|----------|-----|----------|-------|
| Alert rule configurada en Grafana (umbral de errores o similar) | 2 | 2 | alert-rules.yaml: ≥2 eventos "scraper_failed" en 10min ✓ |
| ContactPoint configurado (Discord, email, etc.) | 1 | 1 | contact-point.yaml, Discord via env var DISCORD_WEBHOOK_URL ✓ |
| Screenshot o evidencia de notificación recibida | 2 | 2 | hit6-discord-alert.png ✓ |

**TOTAL BONUS Hit #6:** 5 / 5

---

## RESUMEN DE NOTAS — TP2 PARTE 1

| Sección | Peso | Pts obtenidos | Pts máximos |
|---------|------|--------------|-------------|
| Hit #1 — Stack Loki + Promtail + Grafana | 20% | 19 | 20 |
| Hit #2 — Recolección con labels k8s | 15% | 15 | 15 |
| Hit #3 — Scraper → JSON estructurado | 20% | 20 | 20 |
| Hit #4 — LogQL cookbook (5+ queries) | 15% | 15 | 15 |
| Hit #5 — Dashboard provisionado as-code | 20% | 20 | 20 |
| ADR `0007-stack-de-logging.md` | 10% | 8 | 10 |
| **TOTAL** | **100%** | **97** | **100** |
| Bonus Hit #6 — Alertas | +5% | 5 | +5 |

### Nota Final TP2 Parte 1: 9.7 / 10 (con bonus: 10.2)

---

## Devolución General

**Fortalezas:**
```
Retención 168h correctamente configurada. Alert rules provisionadas as-code (alert-rules.yaml,
contact-point.yaml, notification-policy.yaml) — muy pocos grupos lo hacen declarativamente.
CI con gitleaks-action y Kubernetes dry-run es el único grupo con pipeline de validación.
ADR 0007 con 8 alternativas comparadas: profundidad notable.
```

**Puntos a mejorar:**
```
Agregar manifests/grafana-secret.yaml como placeholder commiteado (con admin-password: "")
para documentar la estructura del secret esperado. Pequeño detalle de documentación.
ADR 0007 podría mencionar explícitamente las consecuencias negativas de Loki
(label-first model, no full-text search en body) para preparar el argumento de Parte 4.
```

**Comentarios para el grupo:**
```
Parte 1 casi perfecta. El -1pt es un detalle menor de documentación.
La alerta as-code y el CI son puntos diferenciales respecto a otros grupos.
```
