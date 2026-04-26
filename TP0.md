# TP 0 — Prerrequisitos

## Instalación de k3s y primeros pasos con Kubernetes

**Requisito obligatorio para entregar la Parte 2 del TP 1 (entrega 02/05/2026)**

> Esta guía es **prerrequisito obligatorio de la Parte 2 del TP 1**. Sin haber completado el TP 0 (cluster k3s/k3d funcional + checklist de validación al final), no se acepta la entrega del Hit #8.

---

## ¿Por qué Kubernetes y por qué k3s?

**Kubernetes (k8s)** es el orquestador de contenedores estándar de la industria. Te permite declarar "quiero que esto corra cada hora", "esto necesita 2 réplicas", "este job tiene que reintentarse hasta 3 veces si falla", y el cluster se encarga.

**k3s** es una distribución liviana de Kubernetes (~70 MB de binario) creada por Rancher y donada al CNCF. Es **Kubernetes real** (certificado), no una versión recortada. Lo eligieron porque es lo más simple de levantar localmente sin depender de snap (microk8s) ni de máquinas virtuales (minikube).

Para este TP vamos a usar k3s en **dos sabores** según el sistema operativo:

| Tu sistema | Qué instalás |
|------------|--------------|
| Linux nativo o WSL2 | **k3s** (instalación directa) |
| macOS o Windows sin WSL | **k3d** — que es k3s corriendo adentro de Docker |

**Los manifiestos YAML son idénticos** entre ambos. Solo cambia cómo levantás el cluster y cómo cargás imágenes Docker.

---

## Requisitos previos

- Tener **Docker** instalado y funcionando (lo necesitan para el Hit #7 igual).
  - Verificá con: `docker version` y `docker ps`.
- Tener **kubectl** instalado (CLI oficial de Kubernetes).
  - macOS: `brew install kubectl`
  - Linux: `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && sudo mv kubectl /usr/local/bin/`
  - Windows: `choco install kubernetes-cli` o `scoop install kubectl`
  - Verificá: `kubectl version --client`
- 4 GB de RAM libres. 2 GB de disco libres.

---

## Camino A — Linux nativo o WSL2 (instalación de k3s)

### Paso 1: Instalar k3s

```bash
curl -sfL https://get.k3s.io | sh -
```

Esto te baja el binario, lo deja en `/usr/local/bin/k3s`, lo registra como servicio `systemd`, y lo arranca. Duración: ~30 segundos.

### Paso 2: Verificar que el cluster está vivo

```bash
sudo k3s kubectl get nodes
```

Tenés que ver algo así:

```
NAME            STATUS   ROLES                  AGE   VERSION
mi-laptop       Ready    control-plane,master   12s   v1.32.x+k3s1
```

### Paso 3: Configurar `kubectl` para no necesitar `sudo`

k3s deja el kubeconfig en `/etc/rancher/k3s/k3s.yaml` con permisos restrictivos. Para usar `kubectl` sin `sudo`:

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
chmod 600 ~/.kube/config
```

Verificá:

```bash
kubectl get nodes
```

Si te devuelve el nodo sin pedir `sudo`, ya está.

### Paso 4: Cómo cargar una imagen Docker en k3s

k3s no usa Docker como runtime — usa **containerd**. Por eso, una imagen que construiste con `docker build` no la "ve" k3s automáticamente. Hay que importarla:

```bash
docker save mi-imagen:latest -o mi-imagen.tar
sudo k3s ctr images import mi-imagen.tar
rm mi-imagen.tar
```

Para verificar que la imagen está cargada:

```bash
sudo k3s ctr images list | grep mi-imagen
```

### Paso 5: Tirar abajo k3s cuando termines el TP

```bash
sudo /usr/local/bin/k3s-uninstall.sh
```

Limpia todo: binario, servicio systemd, datos del cluster, redes. Limpio.

---

## Camino B — macOS o Windows (k3d)

### Paso 1: Instalar k3d

**macOS:**
```bash
brew install k3d
```

**Windows (con Chocolatey):**
```powershell
choco install k3d
```

**Windows (con Scoop):**
```powershell
scoop install k3d
```

Verificá:

```bash
k3d version
```

### Paso 2: Crear un cluster k3s adentro de Docker

```bash
k3d cluster create scraper
```

Esto levanta:
- Un container Docker llamado `k3d-scraper-server-0` corriendo k3s.
- Te configura `~/.kube/config` automáticamente para apuntar a este cluster.

Duración: ~30 segundos.

### Paso 3: Verificar el cluster

```bash
kubectl get nodes
```

Debería mostrar `k3d-scraper-server-0` en estado `Ready`.

### Paso 4: Cargar una imagen Docker en k3d

```bash
docker build -t mi-imagen:latest .
k3d image import mi-imagen:latest -c scraper
```

`k3d image import` se encarga de empaquetar la imagen y enviarla al cluster. Mucho más cómodo que el flujo de k3s nativo.

### Paso 5: Tirar abajo el cluster cuando termines

```bash
k3d cluster delete scraper
```

---

## Comandos básicos de kubectl que vas a usar todo el tiempo

| Comando | Qué hace |
|---------|----------|
| `kubectl get nodes` | Lista los nodos del cluster |
| `kubectl get pods` | Lista los pods en el namespace actual |
| `kubectl get pods -A` | Lista los pods de TODOS los namespaces |
| `kubectl get jobs` | Lista los Jobs (tareas one-off) |
| `kubectl get cronjobs` | Lista los CronJobs (tareas programadas) |
| `kubectl describe pod <nombre>` | Muestra detalles + eventos de un pod (útil cuando algo no arranca) |
| `kubectl logs <pod>` | Logs del pod |
| `kubectl logs -f <pod>` | Logs en streaming |
| `kubectl logs -l app=mi-app` | Logs de todos los pods con el label `app=mi-app` |
| `kubectl apply -f archivo.yaml` | Crea/actualiza recursos del archivo |
| `kubectl delete -f archivo.yaml` | Borra los recursos del archivo |
| `kubectl exec -it <pod> -- /bin/sh` | Te abre un shell adentro del pod |
| `kubectl get events --sort-by='.lastTimestamp'` | Eventos del cluster ordenados por fecha (golden para debug) |

---

## Hello world: deployar nginx para validar que todo funciona

Creá un archivo `nginx-test.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-test
  labels:
    app: nginx-test
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
```

Aplicalo:

```bash
kubectl apply -f nginx-test.yaml
```

Esperá a que esté corriendo:

```bash
kubectl get pod nginx-test --watch
# salí con Ctrl+C cuando veas STATUS=Running
```

Hacé port-forward para probarlo:

```bash
kubectl port-forward pod/nginx-test 8080:80
```

En otra terminal:

```bash
curl http://localhost:8080
```

Tenés que ver el HTML de bienvenida de nginx. Si lo ves, **felicitaciones — tu cluster funciona**.

Limpieza:

```bash
kubectl delete -f nginx-test.yaml
```

---

## Conceptos mínimos que vas a usar en el Hit #8

| Concepto | Para qué sirve |
|----------|----------------|
| **Pod** | La unidad mínima — uno o más containers que comparten red y storage |
| **Job** | Una tarea one-off: corre hasta completarse y termina (ideal para el scraper one-shot) |
| **CronJob** | Una tarea programada: corre cada X tiempo (ideal para "scrapear cada hora") |
| **ConfigMap** | Configuración no-secreta inyectada como env vars o archivos (ej: `BROWSER=chrome`, `HEADLESS=true`) |
| **Secret** | Lo mismo pero para datos sensibles (en este TP no necesitan, pero conviene saber que existe) |
| **PersistentVolumeClaim (PVC)** | Pedido de almacenamiento persistente — k3s te asigna espacio en disco automático con `local-path` |
| **Namespace** | Carpeta lógica del cluster — usen `default` o creen `scraper` para aislar |

No hace falta entender todo de Kubernetes. Para el Hit #8 alcanza con saber qué hace cada uno de estos 6.

---

## Troubleshooting frecuente

### "El pod queda en `Pending` y no arranca"

Casi siempre es porque la imagen no está disponible. En k3s tenés que importar la imagen con `sudo k3s ctr images import`. En k3d con `k3d image import`. Después en el manifiesto del pod usá `imagePullPolicy: IfNotPresent` para que no intente bajarla de Docker Hub.

```bash
kubectl describe pod <nombre>
# leé la sección "Events" — ahí dice qué está fallando
```

### "El pod arranca pero falla con `CrashLoopBackOff`"

Es un error del proceso adentro del container. Mirá los logs:

```bash
kubectl logs <pod>
kubectl logs <pod> --previous   # logs de la corrida anterior si ya reinició
```

### "kubectl no encuentra el cluster (`The connection to the server localhost:8080 was refused`)"

Tu `~/.kube/config` no apunta al cluster correcto. En k3s seguí el Paso 3 del Camino A. En k3d corré `k3d kubeconfig merge scraper --kubeconfig-switch-context`.

### "k3s consume mucha RAM"

k3s idle anda en ~400-500 MB. Si tenés problemas, asegurate de no tener microk8s, minikube ni Docker Desktop con su Kubernetes activo en paralelo.

---

## Lectura recomendada (NO obligatoria)

- **k3s docs** — <https://docs.k3s.io/>
- **k3d docs** — <https://k3d.io/>
- **Kubernetes Patterns** (Bilgin Ibryam, Roland Huß) — Capítulos 1, 2, 7 (Job/CronJob), 9 (ConfigMap)
- **Kubernetes en una hoja** — <https://kubernetes.io/docs/reference/kubectl/quick-reference/>

---

## Validación obligatoria previa al Hit #8

Para que la entrega de la Parte 2 sea aceptada, tienen que poder responder afirmativamente a las 4 preguntas. **Documenten en el README de la Parte 2 (sección "Prerrequisitos cumplidos") la evidencia de cada checkpoint** (output del comando o screenshot).

- [ ] `kubectl get nodes` me devuelve un nodo en `Ready`.
- [ ] Pude correr el nginx-test y abrirlo con `curl localhost:8080`.
- [ ] Sé importar una imagen Docker al cluster (`k3s ctr images import` / `k3d image import`).
- [ ] Entiendo qué es un Pod, un Job, un CronJob, un ConfigMap y un PVC (al menos a nivel "para qué sirve").

Si las 4 son sí, están listos para el Hit #8.
