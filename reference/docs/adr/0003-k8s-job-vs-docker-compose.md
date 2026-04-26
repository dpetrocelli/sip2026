# 0003 — Usar Kubernetes Job + CronJob (k3s/k3d) en lugar de docker-compose con cron del host

- **Date:** 2026-04-26
- **Status:** Accepted
- **Deciders:** Cátedra SIP 2026

## Contexto

El scraper del Hit #8 tiene dos modos de ejecución: **one-shot** (correr una vez los 3 productos y terminar) y **programado** (correr cada hora, conservando histórico). Esto es un patrón clásico de batch job, y hay tres formas razonables de orquestarlo:

1. **docker-compose con `restart: unless-stopped` + entrypoint que loopea con `sleep 3600`.** Funciona, pero el "scheduler" es un `sleep` dentro del contenedor: si la corrida previa falla a mitad y deja el proceso colgado, no hay retry; si el contenedor crashea, `docker-compose` lo reinicia pero no hay backoff; no hay separación entre "definición del job" y "ejecuciones del job"; observabilidad nula.
2. **cron del host disparando `docker run` cada hora.** Acopla el scraping a la máquina específica donde corre el cron; no es declarativo (la "configuración" vive en `/etc/crontab`); imposible de versionar limpiamente; cualquier migración de máquina rompe el scheduling.
3. **Kubernetes `Job` (one-off) + `CronJob` (programado), corriendo en k3s o k3d.** Declarativo (`kubectl apply -f k8s/`); retries con backoff nativos (`backoffLimit`, `restartPolicy: OnFailure`); cleanup automático de pods completados (`successfulJobsHistoryLimit`); observabilidad estándar (`kubectl logs`, `kubectl get jobs --watch`); mismas primitivas que producción real en GKE/EKS/AKS.

La consigna del TP exige explícitamente la opción (3). El motivo no es técnico nada más: es **pedagógico**. El salto que el TP busca forzar es el de pasar del **modelo imperativo** ("yo le digo a la máquina qué comandos correr y cuándo") al **modelo declarativo** ("yo describo el estado deseado y el orquestador converge"). Ese cambio mental es la base de toda la operación de infraestructura moderna (Terraform, Kubernetes, Pulumi, Crossplane), y es muchísimo más útil aprenderlo en un TP de scraping que recién en el primer trabajo.

## Decisión

Empaquetamos el scraper como `Job` (one-off, 8.1) y `CronJob` (programado, 8.2) de Kubernetes, con la configuración externalizada en un `ConfigMap` (8.3) y los outputs persistidos en un `PersistentVolumeClaim` con storage class `local-path` (8.4). El cluster destino es **k3s nativo** o **k3d** (k3s en Docker), que k3s trae listas para usar las primitivas necesarias sin agregar operadores ni Helm charts.

## Consecuencias

- **Más fácil:** retries con `backoffLimit` y backoff exponencial nativo; cleanup automático de jobs viejos (`ttlSecondsAfterFinished`); scheduling declarativo (`schedule: "0 * * * *"` en YAML, no en `/etc/crontab`); mismas APIs que producción seria; transición trivial a EKS/GKE — es el mismo YAML cambiando solamente la `storageClassName`.
- **Más difícil:** stack más pesado (k3s/k3d en vez de solo Docker); requiere completar el TP 0 (prerrequisitos de Kubernetes) antes de empezar; curva de aprendizaje real para alumnos que nunca tocaron Kubernetes; hay que cargar la imagen Docker en el cluster (`k3d image import` o `k3s ctr images import`), paso que no existe con docker-compose.
- **Punto pedagógico (no es accidental):** el TP exige este salto explícitamente. El alumno termina sabiendo escribir manifests de Kubernetes desde cero, validarlos con `kubectl apply --dry-run=client`, y debuggear pods con `kubectl logs` y `kubectl describe`. Esas habilidades transfieren directo al primer trabajo en cualquier empresa que use orquestadores.
- **Riesgo (k3s vs k3d):** algunas diferencias finas en el manejo de imágenes locales y storage. Mitigado con un recetario explícito en el README (Hit #8) que cubre ambos paths.

## Referencias

- Kubernetes Jobs: <https://kubernetes.io/docs/concepts/workloads/controllers/job/>
- Kubernetes CronJobs: <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
- k3s — Lightweight Kubernetes: <https://docs.k3s.io/>
- k3d — k3s in Docker: <https://k3d.io/>
- Burns, Grant, Oppenheimer, Brewer, Wilkes — *Borg, Omega, and Kubernetes*, ACM Queue, 2016: <https://queue.acm.org/detail.cfm?id=2898444>
- ADR 0001 y 0002 (Selenium multi-browser) — el contenedor que se ejecuta en estos Jobs es la imagen del Hit #7, que ya empaqueta Chrome + Firefox + drivers.
