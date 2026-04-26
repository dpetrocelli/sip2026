# Hit #8 — Despliegue en Kubernetes (k3s / k3d)

Despliegue del scraper como `Job` (one-off) y `CronJob` (programado) en un cluster Kubernetes liviano (k3s o k3d).

> **Pre-requisito**: tener un cluster k3s/k3d funcionando. Si no, seguí primero el [TP 0](https://dpetrocelli.github.io/sip2026/practica-0.html).

## Manifiestos en `k8s/`

| Archivo | Recurso | Para qué |
|---------|---------|----------|
| `namespace.yaml` | `Namespace ml-scraper` | Aísla todos los recursos del scraper |
| `configmap.yaml` | `ConfigMap scraper-config` | Variables de entorno: `BROWSER`, `HEADLESS`, `LOG_LEVEL`, `PRODUCTS` (lista) |
| `pvc.yaml` | `PVC scraper-output` (1Gi, `local-path`, RWO) | Almacenamiento persistente de los JSON |
| `job.yaml` | `Job scraper-once` | Corrida one-off con `backoffLimit: 2` |
| `cronjob.yaml` | `CronJob scraper-hourly` | Schedule `0 * * * *` (cada hora) |

Buenas prácticas aplicadas:
- Labels Kubernetes oficiales (`app.kubernetes.io/*`) en todos los recursos.
- `securityContext`: `runAsNonRoot: true`, `runAsUser: 1000`, `allowPrivilegeEscalation: false`.
- Resource `requests`/`limits` en cada container (mem 512Mi, cpu 500m).
- ConfigMap **inmutable** (`immutable: true`).
- `successfulJobsHistoryLimit: 3`, `failedJobsHistoryLimit: 1` en el CronJob para que no se acumulen pods completados.

## Recetario completo

### 1. Construir la imagen Docker

```bash
# Desde la raíz del repo de referencia
docker build -t ml-scraper:latest .
```

### 2. Cargar la imagen en el cluster

**k3s nativo (Linux/WSL):**
```bash
docker save ml-scraper:latest -o ml-scraper.tar
sudo k3s ctr images import ml-scraper.tar
rm ml-scraper.tar
```

**k3d (cualquier OS):**
```bash
k3d image import ml-scraper:latest -c <nombre-del-cluster>
```

### 3. Aplicar los manifiestos (en orden)

El namespace tiene que existir antes que los recursos que lo usan:

```bash
kubectl apply -f hit8/k8s/namespace.yaml
kubectl apply -f hit8/k8s/
```

### 4. Verificar el `Job` one-off

```bash
kubectl wait --for=condition=complete job/scraper-once --timeout=300s -n ml-scraper
kubectl get jobs -n ml-scraper
kubectl logs -l job-name=scraper-once -n ml-scraper
```

Output esperado: el Job en estado `Complete 1/1` y los logs mostrando los 3 productos scrapeados.

### 5. Verificar los JSON generados en el PVC

```bash
# Crear un debug pod que monte el PVC y lea los archivos
kubectl run pvc-debug -n ml-scraper --rm -it --restart=Never \
  --image=alpine --overrides='
{
  "spec": {
    "containers": [{
      "name": "pvc-debug",
      "image": "alpine",
      "command": ["sh"],
      "stdin": true,
      "tty": true,
      "volumeMounts": [{"name":"output","mountPath":"/app/output"}]
    }],
    "volumes": [{"name":"output","persistentVolumeClaim":{"claimName":"scraper-output"}}]
  }
}'
# adentro del pod:
ls -la /app/output
cat /app/output/bicicleta_rodado_29.json | head -20
```

### 6. Verificar el `CronJob`

```bash
kubectl get cronjobs -n ml-scraper
# Output esperado: scraper-hourly  0 * * * *  False  0  <none>  Xs

# Si querés esperar a que dispare una corrida (puede ser hasta 60 min):
kubectl get jobs -n ml-scraper --watch

# O forzá una corrida manual a partir del CronJob:
kubectl create job scraper-manual --from=cronjob/scraper-hourly -n ml-scraper
```

### 7. Cleanup

```bash
kubectl delete -f hit8/k8s/
```

## Cómo cambiar el schedule del CronJob

Editá `cronjob.yaml`:

```yaml
spec:
  schedule: "*/15 * * * *"   # cada 15 minutos
  # o
  schedule: "0 9-18 * * 1-5"  # cada hora de 9 a 18, lun-vie
```

Y reaplicá: `kubectl apply -f hit8/k8s/cronjob.yaml`.

## Cómo escalar

`Job` y `CronJob` no escalan con réplicas como un `Deployment`. Si querés paralelizar el scraping (ej: 3 pods, uno por producto), agregás:

```yaml
spec:
  parallelism: 3
  completions: 3
```

Y el código del scraper tiene que leer un índice (`$JOB_COMPLETION_INDEX`) para decidir qué producto le toca.

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|---------------|-----|
| Pod en `Pending` indefinido | PVC no se pudo bindear | `kubectl describe pvc scraper-output -n ml-scraper` — fijate si hay storageClass `local-path` instalada (k3s/k3d la traen built-in) |
| Pod en `ImagePullBackOff` | La imagen no está en el cluster | Reimportá: `k3d image import ml-scraper:latest -c <cluster>` o `sudo k3s ctr images import` para k3s nativo |
| Job en `Failed` con backoffLimit alcanzado | El scraper se cae 3 veces seguidas | `kubectl logs -l job-name=scraper-once -n ml-scraper --previous` para ver el último error. Probable: ML detectó headless, falta UA custom |
| CronJob no dispara | `suspend: true` por error | `kubectl patch cronjob scraper-hourly -n ml-scraper -p '{"spec":{"suspend":false}}'` |
| `Error from server (NotFound): namespaces "ml-scraper" not found` | Aplicaste todo de una y el namespace todavía no existía | Aplicá `namespace.yaml` primero, después el resto |

## Validación de referencia (cátedra)

Test E2E real ejecutado contra MercadoLibre desde el cluster `k3d-scraper-ref`, con la imagen `ml-scraper:latest` construida desde este Dockerfile (Google Chrome 147 + chromedriver 147 + firefox-esr + geckodriver 0.36):

| Step | Resultado |
|------|----------:|
| Cluster `k3d-scraper-ref` creado | ✅ |
| Imagen real `ml-scraper:latest` construida e importada | ✅ |
| `kubectl apply -f hit8/k8s/` | ✅ 5/5 recursos |
| `Job scraper-once` ejecutado con scraping real contra ML | ✅ |
| 3 productos × 10 resultados scrapeados → JSON en PVC | ✅ |
| `CronJob scraper-hourly` registrado con schedule `0 * * * *` | ✅ |
| Cleanup `kubectl delete -f hit8/k8s/` | ✅ |

### Lecciones aprendidas en la validación

| Síntoma | Causa raíz | Fix aplicado |
|---|---|---|
| Pod `OOMKilled` con `exit 137` ni bien arrancaba Chrome | `resources.limits.memory: 512Mi` insuficiente para Chrome headless con 3 productos | Subido a `requests: 768Mi / limits: 1536Mi` |
| `chrome_crashpad_handler: --database is required` | Bug del paquete `chromium` de Debian trixie con headless | Reemplazado por `google-chrome-stable` desde el repo oficial de Google |
| `cannot touch '/home/scraper/.local/share/applications/mimeapps.list'` | Usuario `scraper` creado con `--no-create-home` → Chrome no podía inicializar | `useradd --create-home` + `chown -R` del home dir |
| Filtros `nuevo` / `tienda_oficial` / `mas_relevantes` no aparecen en algunas búsquedas | ML ajusta los filtros del sidebar según la query (no es bug, es comportamiento real del sitio) | El scraper loggea WARNING y continúa — el JSON se escribe igual con todos los resultados sin filtrar |
