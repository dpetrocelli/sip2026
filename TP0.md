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

## Aviso importante: cómo va a vivir este cluster en tu máquina

Lo que vamos a montar acá es la forma **más simple posible** de tener Kubernetes corriendo. Es perfecto para aprender, pero tiene implicaciones que conviene entender **antes** de empezar:

- **Tu máquina cumple los dos roles a la vez:**
  - **Control plane** — el cerebro del cluster: API server, scheduler, controllers, etcd. Es el que recibe tus `kubectl apply`, decide dónde corre cada pod, y mantiene el "estado deseado" del sistema.
  - **Worker node** — donde efectivamente corren los containers de tus pods.

  En un cluster de producción estos roles están **separados** en máquinas distintas, con varios nodos cada uno, para tener tolerancia a fallos y poder escalar. Acá los junta uno solo: tu laptop.

- **El cluster se muere si apagás la máquina.** k3s queda registrado como servicio `systemd` y arranca solo al boot, pero si suspendés el equipo, hibernás, o reiniciás bruscamente, los pods se pierden hasta que vuelva el servicio. Los Jobs/CronJobs se reanudan recién cuando el cluster vuelva a estar arriba. **Esto NO es una limitación de Kubernetes** — es la limitación de correrlo sobre un solo nodo, en tu máquina, sin alta disponibilidad.

- **No es producción, pero es Kubernetes real.** Los manifiestos que vas a escribir (`Deployment`, `Service`, `Job`, `CronJob`, `ConfigMap`, `PVC`) son **idénticos** a los que usarías en GKE / EKS / AKS o en un k3s multi-nodo desplegado en VPSs. La única diferencia es que en producción ese mismo `kubectl apply -f` lo recibe un cluster distribuido y replicado, en lugar de tu notebook.

### Por qué este TP exige esto y no un `docker-compose`

El objetivo no es "que el scraper corra en algún lado". Es que empiecen a **pensar en términos de Kubernetes**, que es donde la industria está parada hoy. Eso significa entender la diferencia entre:

| Mundo Docker / docker-compose | Mundo Kubernetes |
|------------------------------|------------------|
| `docker run` | `Pod` (la unidad mínima — uno o varios containers que comparten red y storage) |
| `restart: always` en compose | `Deployment` (mantiene N réplicas vivas) |
| `docker run --rm scraper` | `Job` (one-off batch que corre hasta completarse) |
| `cron` en el host disparando `docker run` | `CronJob` (cron nativo del cluster) |
| `volumes:` en compose | `PersistentVolumeClaim` (PVC) — un pedido de almacenamiento desacoplado del nodo |
| Archivo `.env` montado | `ConfigMap` (configuración) + `Secret` (datos sensibles) |
| `ports:` en compose | `Service` (abstracción de red estable sobre pods que pueden morir y revivir) |
| `docker network` | `Namespace` + políticas de red |

Cuando en el **Hit #8** conviertan el `docker run` del Hit #7 en un `Job` + `CronJob` + `ConfigMap` + `PVC`, **ese ejercicio mental es el verdadero aprendizaje del TP** — más que los YAMLs en sí. Pasar de "tengo un Dockerfile y un compose" a "tengo manifiestos declarativos que cualquier cluster Kubernetes puede ejecutar" es el salto profesional que se les pide.

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

## Camino C — Cargar la imagen vía registry público (recomendado para entrega)

Los Pasos 4 de los Caminos A y B (`k3s ctr import` / `k3d image import`) sirven para **vos en tu máquina**. Pero para que **los profesores puedan correr tu Hit #8 sin tener tu imagen local**, necesitás que la imagen esté en algún lugar público que cualquiera pueda hacer `docker pull`.

Para este TP usamos **GitHub Container Registry** (`ghcr.io`): es gratis para imágenes públicas, **no tiene rate limit de pulls** (al contrario de Docker Hub free tier que limita a 100-200/6h y se siente en CI), y la autenticación reusa el `GITHUB_TOKEN` que ya viene con cualquier repo en GitHub.

> ⚠️ **Esto es solo para la demo / entrega del TP.** En producción real las imágenes nunca van a un registry público — van a uno **privado / interno** del equipo (control de seguridad, control de quién hace pull/push, no exponer el código vía las layers, evitar dependencia de un servicio externo). Más abajo hay una tabla con las opciones de registry profesional 2026.

### Push manual a `ghcr.io` (la primera vez)

```bash
# 1. Generá un Personal Access Token (PAT) con scope write:packages:
#    GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
#    Tildá: write:packages, read:packages, delete:packages
#    Copiá el token (lo vas a ver una sola vez).

# 2. Login a ghcr.io con el PAT
export GHCR_PAT=<pegá-el-token>
echo $GHCR_PAT | docker login ghcr.io -u <tu-usuario-github> --password-stdin

# 3. Tagear la imagen con el path completo
docker tag ml-scraper:latest ghcr.io/<tu-usuario>/ml-scraper:latest

# 4. Push
docker push ghcr.io/<tu-usuario>/ml-scraper:latest

# 5. En GitHub: ir a la pestaña "Packages" del repo → click en el package →
#    "Package settings" → "Change visibility" → Public.
#    (las imágenes son privadas por default; sin esto, kubectl no podrá pull desde el cluster)
```

En el manifest del Hit #8, cambiás:

```yaml
containers:
  - name: scraper
    image: ghcr.io/<tu-usuario>/ml-scraper:latest
    imagePullPolicy: Always   # importante: ahora sí queremos que k8s vaya al registry
```

Y eliminás el paso de `k3s ctr import` / `k3d image import` — k8s va a bajar la imagen directo del registry.

### CI auto-push de la imagen al registry (recomendado)

En lugar de pushear a mano, el workflow del Hit #7 puede empujar la imagen en cada merge a `main`:

```yaml
# .github/workflows/scrape.yml — extracto
- name: Login to ghcr.io
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}   # provisto por GH Actions, sin setup

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
    tags: |
      ghcr.io/${{ github.repository_owner }}/ml-scraper:latest
      ghcr.io/${{ github.repository_owner }}/ml-scraper:${{ github.sha }}
```

Después de merguear a main, la imagen está disponible automáticamente para `kubectl apply`.

---

## Container registries — el panorama 2026

Para que tengan idea de cómo se hace esto en la industria, no solo en el TP:

| Registry | Tipo | Cuándo se elige | Free tier para públicas |
|---|---|---|:---:|
| **GitHub Container Registry** (`ghcr.io`) | Cloud, integrado con GitHub | Stack basado en GitHub Actions, OSS, ergonomía top | ✅ ilimitado |
| **Docker Hub** (`docker.io`) | Cloud, el original | Imágenes oficiales para discoverability máxima | ⚠️ free tier limita pulls a 100/6h anónimo, 200/6h autenticado — **se siente en CI**, por eso para este TP usamos `ghcr.io` |
| **Amazon ECR** | Cloud, AWS-native | Workloads en EKS / ECS / Fargate; necesitás IAM-based auth | ❌ pago (pricing por GB-mes + transferencia) |
| **Google Artifact Registry** (reemplazó GCR) | Cloud, GCP-native | GKE / Cloud Run; soporta OCI + Maven + npm en un mismo registry | ❌ pago |
| **Azure Container Registry** | Cloud, Azure-native | AKS, integración con Azure DevOps | ❌ pago (3 tiers: Basic / Standard / Premium) |
| **GitLab Container Registry** | Cloud o self-hosted | Stack basado en GitLab CI | ✅ con cuenta GitLab |
| **Harbor** | **Self-hosted, OSS** (CNCF graduated) | El estándar on-prem corporativo: replicación, vulnerability scan, RBAC | N/A — vos lo hosteás |
| **JFrog Artifactory** | Self-hosted o cloud, enterprise | Multi-format (Docker + Maven + npm + Helm + Conda + ...) en un solo lugar | ❌ pago (excepto OSS edition) |
| **Quay.io** (Red Hat) | Cloud o self-hosted, OSS-friendly | Open source projects que quieren OSS-aligned hosting | ✅ públicas |
| **Sonatype Nexus Repository** | Self-hosted | Alternativa a Artifactory; multi-format | ✅ OSS edition |

**Reglas de decisión rápidas (2026):**

- **¿Imagen pública para que cualquiera la use?** → `ghcr.io` (si es OSS en GitHub) o Docker Hub (si querés discoverability máxima).
- **¿Workload en una sola nube?** → el registry nativo de esa nube (ECR / GAR / ACR). Ahorra latencia y a veces dinero en transferencia.
- **¿On-prem / multi-nube / requisitos de soberanía?** → **Harbor** es la respuesta más común. Es CNCF graduated, tiene replicación, escaneo de vulnerabilidades (Trivy / Clair), RBAC, GC, signing.
- **¿Stack monorepo Maven + npm + Docker + Helm?** → Artifactory o Nexus.

**Lecturas útiles:**
- [The 2024 State of Container Registries — CNCF](https://www.cncf.io/reports/state-of-container-registries/) (la edición 2026 sale a fin de año)
- [Harbor docs](https://goharbor.io/docs/) — para entender qué hace un registry de producción que un public hub no
- [OCI Distribution Spec](https://github.com/opencontainers/distribution-spec) — el protocolo HTTP estándar que hablan todos los registries OCI-compliant (saber esto te abre el mercado entero)
- [Sigstore / cosign](https://docs.sigstore.dev/) — firma criptográfica de imágenes (lo que viene como **estándar 2026** para supply chain security; ya es parte de SLSA Level 3)

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

## Lectura recomendada y referencias

> No es lectura obligatoria, pero si van en serio con esto, las primeras 4-5 referencias les van a ahorrar meses.

### Documentación oficial (lo que conviene tener bookmarkeado)

- **Kubernetes — sitio oficial** — <https://kubernetes.io/>
- **Conceptos de Kubernetes** — <https://kubernetes.io/docs/concepts/> (Pod, Deployment, Service, Job, CronJob, ConfigMap, PVC explicados por la fuente)
- **API Reference** — <https://kubernetes.io/docs/reference/kubernetes-api/> (todos los campos de cada manifiesto)
- **kubectl cheatsheet** — <https://kubernetes.io/docs/reference/kubectl/quick-reference/>
- **k3s docs** — <https://docs.k3s.io/>
- **k3d docs** — <https://k3d.io/>
- **CNCF Landscape** — <https://landscape.cncf.io/> (mapa de ~1500 proyectos del ecosistema cloud-native — útil para ubicar herramientas en contexto)
- **KEPs (Kubernetes Enhancement Proposals)** — <https://github.com/kubernetes/enhancements/tree/master/keps> (cómo evoluciona Kubernetes — útil cuando quieren entender por qué algo funciona como funciona)

### Libros — ordenados de "primer contacto" a "producción/avanzado"

| Libro | Autores | Editorial / Año | Cuándo leerlo |
|-------|---------|-----------------|---------------|
| [The Kubernetes Book (3rd ed)](https://www.oreilly.com/library/view/the-kubernetes-book/9781805806639/) | Nigel Poulton, Pushkar Joglekar | O'Reilly · 2024 | El más amigable — primer contacto, lectura de fin de semana |
| [Kubernetes: Up and Running (3rd ed)](https://www.oreilly.com/library/view/kubernetes-up-and/9781098110192/) | Brendan Burns (co-creador de k8s), Joe Beda, Kelsey Hightower, Lachlan Evenson | O'Reilly · 2022 | Intro canónica — escrita por quienes diseñaron k8s |
| [Kubernetes in Action (2nd ed)](https://www.manning.com/books/kubernetes-in-action-second-edition) | Marko Lukša, Kevin Conner | Manning · 2026 | El **best of class** para deep-dive. ⭐ Recomendación principal si solo van a leer uno |
| [Kubernetes Patterns (2nd ed)](https://www.oreilly.com/library/view/kubernetes-patterns-2nd/9781098131678/) | Bilgin Ibryam, Roland Huß | O'Reilly · 2023 | Patterns reutilizables — Cap. 7 (Batch Job), 8 (Periodic Job) son **directamente** lo que van a hacer en el Hit #8 |
| [Kubernetes Best Practices (2nd ed)](https://www.oreilly.com/library/view/kubernetes-best-practices/9781098142155/) | Brendan Burns et al | O'Reilly · 2024 | Operación en producción: RBAC, observabilidad, GitOps, networking |
| [Cloud Native Patterns](https://www.manning.com/books/cloud-native-patterns) | Cornelia Davis | Manning · 2019 | Patrones cloud-native independientes de k8s — útil para entender el "por qué" detrás de los manifiestos |
| [GitOps and Kubernetes](https://www.manning.com/books/gitops-and-kubernetes) | Billy Yuen, Alexander Matyushentsev, Todd Ekenstam, Jesse Suen | Manning · 2021 | Si después quieren hacer GitOps con Argo CD / Flux |
| [Programming Kubernetes](https://www.oreilly.com/library/view/programming-kubernetes/9781492047094/) | Michael Hausenblas (AWS), Stefan Schimanski (Red Hat) | O'Reilly · 2019 | Cuando quieran escribir Operators / CRDs propios |
| [CKA Study Guide (2nd ed)](https://www.oreilly.com/library/view/cka-study-guide/9781098140502/) | Benjamin Muschko | O'Reilly · enero 2026 (v1.33) | Si apuntan a la certificación CKA — el primer libro alineado al examen actualizado |

### Papers fundacionales — el ADN intelectual de Kubernetes

Los conceptos de Job, CronJob, scheduling, PVC, etc. no salieron de la nada — vienen de 15 años de investigación y operación a escala en Google con sus sistemas Borg y Omega. Estos 4 papers son **lectura obligatoria conceptual** para cualquiera que quiera entender el "por qué" detrás de Kubernetes:

- **Burns, Grant, Oppenheimer, Brewer, Wilkes (2016).** "Borg, Omega, and Kubernetes: Lessons learned from three container-management systems over a decade". *ACM Queue / Communications of the ACM*. — <https://queue.acm.org/detail.cfm?id=2898444>
  > El paper que conecta los puntos: por qué Kubernetes es como es. **Léanlo aunque sea uno solo.**

- **Verma, Pedrosa, Korupolu, Oppenheimer, Tune, Wilkes (2015).** "Large-scale cluster management at Google with Borg". *EuroSys 2015*. — <https://research.google.com/pubs/archive/43438.pdf>
  > El paper original de Borg, el sistema interno de Google que inspiró Kubernetes. Estructura de control plane, scheduling, admission control.

- **Schwarzkopf, Konwinski, Abd-El-Malek, Wilkes (2013).** "Omega: flexible, scalable schedulers for large compute clusters". *EuroSys 2013*. — <https://research.google/pubs/omega-flexible-scalable-schedulers-for-large-compute-clusters/>
  > Schedulers paralelos optimistic — la base conceptual del scheduler de Kubernetes.

- **Tirmazi, Barker, Deng, Haque, Qin, Hand, Harchol-Balter, Wilkes (2020).** "Borg: the Next Generation". *EuroSys 2020*. — <https://dl.acm.org/doi/10.1145/3342195.3387517>
  > Análisis empírico de cómo evolucionó Borg después de 5 años más de operación. Datos de utilización, mix de workloads, lecciones aprendidas.

### Recursos comunitarios

- **Kubernetes the Hard Way** — Kelsey Hightower — <https://github.com/kelsey-hightower/kubernetes-the-hard-way>
  > Tutorial canónico para construir un cluster Kubernetes "desde cero" sin instaladores. **No lo necesitan para el TP**, pero si después quieren entender qué hace k3s por debajo, este es el camino.

- **Awesome Kubernetes** — <https://github.com/ramitsurana/awesome-kubernetes> (lista curada de herramientas, charlas, libros)
- **CNCF YouTube** — <https://www.youtube.com/@cncf> (KubeCon talks gratis — buscá "Job", "CronJob", "k3s" para charlas específicas)
- **Learnk8s blog** — <https://learnk8s.io/blog> (artículos técnicos profundos, gratuitos)
- **Killercoda** — <https://killercoda.com/playgrounds/scenario/kubernetes> (sandbox interactivo en el navegador para practicar `kubectl` sin instalar nada)

---

## Validación obligatoria previa al Hit #8

Para que la entrega de la Parte 2 sea aceptada, tienen que poder responder afirmativamente a las 4 preguntas. **Documenten en el README de la Parte 2 (sección "Prerrequisitos cumplidos") la evidencia de cada checkpoint** (output del comando o screenshot).

- [ ] `kubectl get nodes` me devuelve un nodo en `Ready`.
- [ ] Pude correr el nginx-test y abrirlo con `curl localhost:8080`.
- [ ] Sé importar una imagen Docker al cluster (`k3s ctr images import` / `k3d image import`).
- [ ] Entiendo qué es un Pod, un Job, un CronJob, un ConfigMap y un PVC (al menos a nivel "para qué sirve").

Si las 4 son sí, están listos para el Hit #8.
