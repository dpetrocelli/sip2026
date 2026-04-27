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

## Histórico con PostgreSQL — implementación de referencia

> **Estado:** _skeleton_. Los manifests, el schema y el módulo Python están listos. La integración con `main.py` (llamar a `PostgresWriter.insert_results()` después de cada scrape) queda **a cargo del alumno** como parte de su Hit #8.

### Qué incluye este skeleton

| Archivo | Recurso / Tipo | Para qué |
|---------|----------------|----------|
| `k8s/postgres-secret.yaml` | `Secret` Opaque | Guarda `POSTGRES_PASSWORD`. **Solo TP** — para producción ver external-secrets / sealed-secrets / Vault. |
| `k8s/postgres-init-configmap.yaml` | `ConfigMap` `postgres-init-sql` | Schema inicial (`init.sql`) montado en `/docker-entrypoint-initdb.d/` — Postgres lo ejecuta automáticamente al primer arranque. |
| `k8s/postgres-statefulset.yaml` | `StatefulSet` `postgres` (1 réplica) | Postgres 16 (`postgres:16-trixie`) con PVC 5 Gi (`local-path`), corre como UID 999 non-root. |
| `k8s/postgres-service.yaml` | `Service` ClusterIP `postgres:5432` | Endpoint interno del cluster. El scraper se conecta a `postgres.ml-scraper.svc.cluster.local`. |
| `migrations/001_initial_schema.sql` | SQL versionado | Fuente de verdad del schema. Mismo contenido que el `data.init.sql` del ConfigMap (mantenerlos sincronizados). |
| `postgres_writer.py` | Módulo Python | `class PostgresWriter` con pool de conexiones (`psycopg_pool`), `insert_results()` y retry con backoff exponencial reusando `hit5/retry.py`. |

### Schema (resumen)

```sql
CREATE TABLE scrape_results (
    id              BIGSERIAL PRIMARY KEY,
    producto        TEXT NOT NULL,
    titulo          TEXT NOT NULL,
    precio          NUMERIC(12,2),
    link            TEXT,
    tienda_oficial  TEXT,
    envio_gratis    BOOLEAN,
    cuotas_sin_interes TEXT,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- + 2 índices: (producto, scraped_at DESC) y (scraped_at DESC)
```

`scraped_at` lo llena la base con `NOW()` — no se manda desde Python, así evitamos drift de reloj entre nodos del cluster.

### Cómo deployar

```bash
# 1. El namespace ya está creado por hit8/k8s/namespace.yaml. Si no:
kubectl apply -f hit8/k8s/namespace.yaml

# 2. Aplicar los 4 manifests de Postgres (orden recomendado):
kubectl apply -f hit8/k8s/postgres-secret.yaml
kubectl apply -f hit8/k8s/postgres-init-configmap.yaml
kubectl apply -f hit8/k8s/postgres-statefulset.yaml
kubectl apply -f hit8/k8s/postgres-service.yaml

# 3. Esperar a que Postgres esté Ready (puede tardar ~30-60s la primera vez,
#    porque tiene que inicializar el cluster y aplicar el init.sql):
kubectl wait --for=condition=Ready pod/postgres-0 -n ml-scraper --timeout=180s
```

### Cómo conectarse desde el scraper

Dentro del cluster, el hostname del Service es lo que resuelve a la IP de Postgres:

```python
import os
from hit8.postgres_writer import PostgresWriter

# El hostname `postgres` resuelve dentro del namespace ml-scraper.
# El password viene del Secret (montar como env var en el Job/CronJob).
dsn = f"postgresql://scraper:{os.environ['POSTGRES_PASSWORD']}@postgres:5432/scraper"

with PostgresWriter(dsn) as writer:
    n = writer.insert_results(
        producto="Bicicleta rodado 29",
        items=resultados,  # list[dict] del scraper
    )
    print(f"Persistidos {n} resultados")
```

Para que el `Job`/`CronJob` reciba `POSTGRES_PASSWORD`, agregar al spec del container:

```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-secret
        key: POSTGRES_PASSWORD
```

### Verificar que las inserciones aterrizan

```bash
# Abrir un psql interactivo dentro del pod:
kubectl exec -it -n ml-scraper postgres-0 -- psql -U scraper -d scraper

# Ya en el prompt psql:
SELECT producto, COUNT(*) AS n, MAX(scraped_at) AS ultima
FROM scrape_results
GROUP BY producto
ORDER BY ultima DESC;

-- Top 5 más baratos del último scrape de un producto:
SELECT titulo, precio, tienda_oficial, scraped_at
FROM scrape_results
WHERE producto = 'Bicicleta rodado 29'
ORDER BY scraped_at DESC, precio ASC
LIMIT 5;
```

O desde fuera del cluster con port-forward:

```bash
kubectl port-forward -n ml-scraper svc/postgres 5432:5432
# en otra terminal:
psql "postgresql://scraper:changeme-en-prod@localhost:5432/scraper" \
  -c "SELECT COUNT(*) FROM scrape_results;"
```

### Lo que falta (a cargo del alumno en su Hit #8)

1. Agregar `psycopg[binary]` y `psycopg_pool` a `requirements.txt` / `pyproject.toml`.
2. Importar `PostgresWriter` desde `main.py` y llamarlo después de cada scrape exitoso.
3. Inyectar `POSTGRES_PASSWORD` desde el Secret hacia el container del scraper en `job.yaml` y `cronjob.yaml`.
4. Manejar el caso "Postgres no responde" — el writer ya hace 3 retries con backoff, pero el scraper puede decidir si seguir escribiendo solo el JSON al PVC o abortar.
5. (Opcional) Implementar la **paginación** y las **estadísticas** que pide la consigna del Hit #8 leyendo de `scrape_results`.

### Decisión arquitectónica

Ver [`docs/adr/0007-postgres-statefulset-vs-managed.md`](../docs/adr/0007-postgres-statefulset-vs-managed.md) para el por qué de `StatefulSet` en cluster en lugar de SQLite local, RDS managed, o DynamoDB.
