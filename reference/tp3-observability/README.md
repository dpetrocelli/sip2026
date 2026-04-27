# TP 3 — Logging centralizado con Loki + Alloy + Grafana

Implementación de referencia de la cátedra para el TP 3: capturar los logs del scraper ML (TP1·P2, Hit #4) que corre como `Job`/`CronJob` en k3s/k3d, persistirlos más allá del ciclo de vida del Pod, y consultarlos desde Grafana.

Decisión arquitectónica completa en [ADR 0008](../docs/adr/0008-loki-vs-elk-vs-managed.md).

## Arquitectura

```
                     namespace: ml-scraper                       namespace: observability
                  ┌──────────────────────────┐               ┌────────────────────────────────┐
                  │                          │               │                                │
  ┌─────────┐     │  ┌──────────────────┐    │               │  ┌──────────────────────┐      │
  │ Job /   │────▶│  │ scraper Pod      │    │               │  │ Loki StatefulSet     │      │
  │ CronJob │     │  │ (Selenium+Chrome)│    │               │  │ (SingleBinary, 1x)   │      │
  └─────────┘     │  └──────────────────┘    │               │  │  + PVC local-path 5Gi│      │
                  │           │              │               │  └──────────┬───────────┘      │
                  │           │ stdout/stderr│               │             │                  │
                  │           ▼              │               │             │ HTTP push        │
                  │  /var/log/pods/...log    │               │             │  :3100           │
                  │  (kubelet)               │               │             ▲                  │
                  └───────────┬──────────────┘               │             │                  │
                              │                              │   ┌─────────┴──────────┐       │
                              │ hostPath mount               │   │ Alloy DaemonSet    │       │
                              └─────────────────────────────▶│   │ (1 pod por nodo)   │       │
                                                             │   └──────────┬─────────┘       │
                                                             │              │                 │
                                                             │              │ query           │
                                                             │              ▼                 │
                                                             │   ┌────────────────────┐       │
                                                             │   │ Grafana Deployment │       │
                                                             │   │ NodePort :30000    │◀──────┼── localhost:30000
                                                             │   └────────────────────┘       │
                                                             └────────────────────────────────┘
```

Flujo: el scraper escribe a stdout → kubelet lo persiste en `/var/log/pods/<...>/...log` del nodo → Alloy (DaemonSet, monta hostPath) lee esos archivos → push HTTP a Loki en `loki.observability.svc.cluster.local:3100` → Loki indexa labels y guarda chunks en PVC → Grafana consulta vía LogQL y renderiza el dashboard.

## Estructura del directorio

```
tp3-observability/
├── README.md                         (este archivo)
├── helm/
│   ├── loki-values.yaml              values para chart grafana/loki 6.x
│   ├── grafana-values.yaml           values para chart grafana/grafana 8.x
│   └── alloy-values.yaml             values para chart grafana/alloy 0.x
├── manifests/
│   ├── namespace.yaml                namespace observability con PSS baseline
│   └── grafana-datasource-cm.yaml    ConfigMap con datasource Loki (referencia)
├── dashboards/
│   └── ml-scraper.json               dashboard Grafana (6 paneles)
├── queries/
│   └── logql-cheatsheet.md           10 queries LogQL útiles + sintaxis
└── scraper-json-logging.py           snippet para emitir logs JSON desde main.py
```

## Despliegue paso a paso

### Pre-requisitos

- Cluster k3s o k3d corriendo (`kubectl get nodes` debe responder).
- `helm` 3.x instalado (`helm version`).
- El scraper de TP1·P2 ya desplegado en el namespace `ml-scraper` (ver Hit #5/#6).

### 1. Agregar el repo de Helm de Grafana

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 2. Crear el namespace observability

```bash
kubectl apply -f manifests/namespace.yaml
```

### 3. Crear el Secret con la admin password de Grafana

NO hardcodear en el YAML del repo. Crear con un valor real:

```bash
kubectl -n observability create secret generic grafana-admin \
  --from-literal=admin-user=admin \
  --from-literal=admin-password='CAMBIAR_ESTO_AHORA'
```

### 4. Instalar Loki

Verificar la última versión 6.x del chart antes de instalar:

```bash
helm search repo grafana/loki --versions | head
```

Y deployar (ajustar `--version` con lo que devuelva el comando anterior):

```bash
helm upgrade --install loki grafana/loki \
  -n observability \
  -f helm/loki-values.yaml \
  --version 6.16.0
```

Esperar a que el Pod esté `Ready`:

```bash
kubectl -n observability wait --for=condition=ready pod -l app.kubernetes.io/name=loki --timeout=180s
```

### 5. Instalar Alloy (collector)

```bash
helm search repo grafana/alloy --versions | head
helm upgrade --install alloy grafana/alloy \
  -n observability \
  -f helm/alloy-values.yaml \
  --version 0.9.0
```

Verificar que el DaemonSet tenga 1 Pod por nodo:

```bash
kubectl -n observability get daemonset alloy
kubectl -n observability get pods -l app.kubernetes.io/name=alloy
```

### 6. Instalar Grafana

```bash
helm search repo grafana/grafana --versions | head
helm upgrade --install grafana grafana/grafana \
  -n observability \
  -f helm/grafana-values.yaml \
  --version 8.5.0
```

### 7. Cargar el dashboard del scraper

Crear el ConfigMap con el JSON del dashboard, marcado con la label que el sidecar de Grafana watchea:

```bash
kubectl -n observability create configmap ml-scraper-dashboard \
  --from-file=ml-scraper.json=dashboards/ml-scraper.json

kubectl -n observability label configmap ml-scraper-dashboard \
  grafana_dashboard=1
```

El sidecar lo detecta en ~30 segundos y lo monta en `/var/lib/grafana/dashboards/tp3-default/ml-scraper.json`. Aparece en la UI bajo el folder "TP3 — ML Scraper".

## Acceder a Grafana

Opción A — port-forward (recomendado para todos los entornos):

```bash
kubectl port-forward -n observability svc/grafana 3000:80
```

Abrir <http://localhost:3000>. Login con `admin` y la password que se configuró en el Secret.

Opción B — NodePort (solo en k3d/k3s donde el host alcanza al nodo):

```bash
# El service de Grafana está expuesto en el NodePort 30000 del nodo k3d.
# Listar el mapeo de puertos del cluster k3d:
docker port k3d-mycluster-server-0 30000
# y abrir el puerto que diga (típicamente http://localhost:30000).
```

## Probar que funciona end-to-end

1. Disparar una corrida del scraper:

   ```bash
   kubectl -n ml-scraper create job manual-test --from=cronjob/ml-scraper-cronjob
   kubectl -n ml-scraper logs -f job/manual-test
   ```

2. En Grafana → Explore → seleccionar datasource `Loki` → ejecutar:

   ```logql
   {namespace="ml-scraper"}
   ```

   Deberían aparecer las líneas del scraper en orden inverso. Si no aparecen, ver "Troubleshooting".

3. Abrir el dashboard "ML Scraper — Observabilidad (TP 3)" del folder TP3 — ML Scraper. Los paneles deberían empezar a poblarse.

## Correr una query LogQL desde la línea de comandos (sin Grafana)

Útil para scripting/CI:

```bash
# Port-forward a Loki:
kubectl port-forward -n observability svc/loki 3100:3100 &

# Total de logs en las últimas 24h:
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query=sum(count_over_time({namespace="ml-scraper"} [24h]))' \
  | jq .

# O directamente desde el cluster sin port-forward:
kubectl exec -n observability statefulset/loki -- \
  wget -qO- 'http://localhost:3100/loki/api/v1/query?query=sum(count_over_time({namespace="ml-scraper"}[24h]))'
```

Diez queries más en [`queries/logql-cheatsheet.md`](queries/logql-cheatsheet.md).

## Habilitar el logging JSON en el scraper

Por default el scraper de Hit #4 usa `logging.basicConfig` con formato texto. Para que los labels `level`, `event`, `producto` se promuevan en Loki hay que pasar a JSON.

Ver [`scraper-json-logging.py`](scraper-json-logging.py) — es un snippet de referencia. El alumno tiene que:

1. Agregar `python-json-logger>=2.0.7` a `requirements.txt`.
2. Reemplazar `logging.basicConfig(...)` de `main.py` por la función `setup_json_logging()` del snippet.
3. Cambiar las llamadas `logger.info("=== Producto: %s", p)` por `logger.info("Scraping iniciado", extra={"event": "product_started", "producto": p})`.
4. Rebuildear la imagen y desplegar.

Sin este cambio el dashboard sigue funcionando pero los paneles que usan labels `producto`/`level` van a estar vacíos (los queries que usan `|=` line filter siguen andando).

## Troubleshooting

| Síntoma | Causa probable | Cómo verificar |
|---------|----------------|----------------|
| `{namespace="ml-scraper"}` no devuelve nada | Alloy no descubrió los pods | `kubectl logs -n observability -l app.kubernetes.io/name=alloy` |
| Loki responde 500 al insertar | PVC lleno | `kubectl exec -n observability loki-0 -- df -h /var/loki` |
| Grafana no muestra el dashboard | Sidecar no tomó el ConfigMap | `kubectl logs -n observability deploy/grafana -c grafana-sc-dashboard` |
| Labels `producto`/`level` vacíos | Scraper emite texto, no JSON | Mirar un log con `kubectl logs` — ¿es `[INFO] ...` o `{"level": "INFO", ...}`? |
| Pod de Alloy `CrashLoopBackOff` | PSS restricted bloquea hostPath | `kubectl describe pod -n observability -l app.kubernetes.io/name=alloy` |

## Limpieza

Borrar todo el stack sin tocar el scraper:

```bash
helm uninstall -n observability grafana
helm uninstall -n observability alloy
helm uninstall -n observability loki
kubectl delete configmap -n observability ml-scraper-dashboard grafana-datasource-loki
kubectl delete secret -n observability grafana-admin
kubectl delete namespace observability
```

El namespace `ml-scraper` queda intacto.

## Referencias

- ADR 0008 — Loki vs ELK vs managed: [`../docs/adr/0008-loki-vs-elk-vs-managed.md`](../docs/adr/0008-loki-vs-elk-vs-managed.md)
- Loki docs: <https://grafana.com/docs/loki/latest/>
- Alloy docs: <https://grafana.com/docs/alloy/latest/>
- LogQL cheatsheet (este TP): [`queries/logql-cheatsheet.md`](queries/logql-cheatsheet.md)
