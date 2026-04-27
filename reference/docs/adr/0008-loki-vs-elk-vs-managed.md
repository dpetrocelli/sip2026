# 0008 — Usar Loki + Alloy para logging centralizado en lugar de ELK o un servicio managed

- **Date:** 2026-04-26
- **Status:** Accepted
- **Deciders:** Cátedra SIP 2026

## Contexto

El TP 3 incorpora **logging centralizado** sobre el scraper de TP1·P2 que ya corre como `Job` y `CronJob` en k3s/k3d (decidido en ADR 0003). El problema operacional concreto: cuando un Pod del `CronJob` termina, sus logs viven solamente en `/var/log/pods/<...>/...log` del nodo donde corrió, y son rotados/borrados por kubelet en cuestión de horas. `kubectl logs` deja de servir apenas el Pod desaparece. Para responder preguntas como "¿cuántos scrapes fallaron esta semana?", "¿qué producto está fallando más?", "¿cuál fue la última excepción del CronJob de las 03:00?" necesitamos persistir los logs fuera del ciclo de vida del Pod y poder consultarlos con expresiones más ricas que `grep`.

Las alternativas razonables son cuatro:

1. **Sin centralización (`kubectl logs`).** Cero infraestructura nueva, cero costo. Pero el `CronJob` borra los Pods completados después de `successfulJobsHistoryLimit` (default 3) y los logs se pierden con ellos. No hay forma de hacer queries agregadas. Inviable apenas el TP empieza a producir más de un par de corridas.
2. **ELK / OpenSearch (Elasticsearch + Logstash + Kibana).** El stack clásico, muy potente para búsqueda full-text en datos heterogéneos. Pero indexa cada palabra de cada log en un inverted index, lo cual cuesta caro en RAM y disco — Elasticsearch pide 4-8 GB de heap como mínimo decente, y el stack completo (ES + Logstash + Kibana + 1 nodo de cada) no entra cómodamente en un laptop con 8-16 GB. Además, para el caso de uso del scraper (logs muy estructurados, queries casi siempre filtradas por label `producto`/`level`/`namespace`) el inverted index de full-text es overkill.
3. **Splunk / Datadog / New Relic / Grafana Cloud (managed).** Lo correcto para una empresa con presupuesto y compliance. Pero (a) requiere cuenta + tarjeta de crédito (Datadog ~$0.10/GB ingerido, Splunk mucho más), (b) saca el TP del modelo "todo corre en el laptop del alumno", (c) los free tiers son severamente limitados (Grafana Cloud Free son 50 GB/mes pero exige cuenta y exporta datos del alumno a un tercero), (d) lock-in: las queries SPL/DDQL no son portables.
4. **Loki + Alloy (Grafana stack self-hosted).** Loki indexa solamente los **labels** (`namespace`, `pod`, `container`, `producto`, `level`), no el contenido de los logs — eso lo hace dramáticamente más barato en CPU/RAM/disco que ELK. El cuerpo del log se guarda comprimido en chunks. La consecuencia: las queries por label son baratísimas y las queries por contenido (`|=` line filter) escanean linealmente el chunk, lo cual es OK porque el volumen es chico. Alloy (sucesor unified de Promtail + Grafana Agent + OTel Collector, GA 2024) es el collector recomendado.

El TP está pensado para que cualquier alumno pueda completarlo con un laptop modesto y sin cuentas en cloud — el énfasis está en el **patrón** ("tu app emite logs, ¿cómo los centralizás y los consultás?") y no en el throughput de un sistema productivo. Eso descarta (3) por costo y por foco. ELK (2) se descarta porque el footprint operacional es desproporcionado para el volumen del scraper. La opción (1) es lo que ya tiene el alumno y es justamente lo que el TP busca superar.

## Decisión

Decidimos desplegar **Loki en modo SingleBinary + Alloy como DaemonSet + Grafana** en un namespace dedicado `observability` del mismo cluster k3s/k3d, todo via Helm con values pinneados.

Sub-decisiones:

- **Loki versión:** chart `grafana/loki` 6.x (referencia: 6.16.0). Modo `SingleBinary`, no distributed. 1 réplica, storage `filesystem` sobre PVC `local-path` de 5 Gi.
- **Retention:** 168 horas (7 días). Suficiente para investigar incidentes de la semana sin que el PVC se llene. El compactor de Loki hace garbage collection automático.
- **Alloy versión:** chart `grafana/alloy` 0.x (referencia: 0.9.0). Modo `daemonset` para que cada nodo lea sus propios logs locales. Pipeline mínimo: discovery k8s filtrado al namespace `ml-scraper` + parser JSON + push a Loki.
- **Grafana versión:** chart `grafana/grafana` 8.x (referencia: 8.5.0). Service `NodePort` 30000 para acceso fácil desde el host. Datasource Loki preprovisionado, dashboard del scraper preprovisionado vía sidecar de ConfigMaps.
- **Auth:** `auth_enabled: false` en Loki (un solo tenant `fake`). Admin de Grafana vía Secret externo creado por el alumno.
- **Logs estructurados:** el scraper de TP1·P2 emite JSON con `python-json-logger`, lo cual permite que Alloy promueva `level`, `event`, `producto` a labels Loki sin parseo regex en cada query.

## Consecuencias

- **Lo que se vuelve más fácil:**
  - **Persistencia más allá del Pod:** los logs sobreviven al borrado del Pod del CronJob, durante 7 días. Podemos investigar incidentes de hace 5 días sin haber tenido que prever capturarlos.
  - **Queries agregadas:** con LogQL respondemos preguntas que con `kubectl logs | grep` requieren scripts: % éxito por producto, distribución de duración por Job, top-k errores, comparación día contra día.
  - **Dashboards reproducibles:** el JSON del dashboard está en el repo, se aplica con `kubectl apply -f` (vía ConfigMap), todos los alumnos ven exactamente la misma vista. No hay "el dashboard que armé en mi compu se perdió cuando reinstalé".
  - **Ruta de migración a producción clara:** el mismo stack escala a Grafana Cloud (con `loki.write` apuntando a un endpoint remoto), o a Loki distribuido sobre S3 + memberlist en EKS. El alumno aprende las primitivas reales.

- **Lo que se vuelve más difícil o se sacrifica:**
  - **Más Pods que mantener.** Loki + Alloy + Grafana suman ~3 GB de RAM en steady state al cluster. En un laptop con 8 GB ya con Chrome del scraper + Postgres del Hit #8 + el k3d en sí, es apretado. Mitigado con `requests`/`limits` modestos y advertido en el README.
  - **Search full-text es lineal.** Si en el futuro el alumno quiere buscar una palabra exacta en miles de millones de líneas, Loki no es ELK — escanea cada chunk. Para el TP no importa (volumen chico), pero hay que dejar la limitación documentada.
  - **No hay HA.** SingleBinary con 1 réplica == single point of failure. Si el Pod de Loki muere, hay un gap de logs hasta que el StatefulSet lo levanta. Aceptable para el TP.
  - **Sin auth multi-tenant.** Cualquier cosa que pueda hablar con el Service `loki:3100` puede leer/escribir todos los logs. En el TP eso es solo el cluster local; en cualquier escenario compartido habría que activar `auth_enabled: true` y armar el header `X-Scope-OrgID`.

- **Riesgos conocidos y mitigaciones:**
  - **Cardinality explosion.** Si el scraper o Alloy promueven a label algún campo de alta cardinalidad (ej. `request_id` único por request), Loki crea una serie nueva por cada valor y la ingesta se degrada. Mitigado: el pipeline de Alloy en este TP solo promueve `level`, `event`, `producto` — los tres con cardinalidad acotada. Documentado en `helm/alloy-values.yaml` con un comentario explícito.
  - **PVC se llena antes de los 7 días.** Si el scraper genera más logs de lo esperado (ej. un loop de errores con stacktraces enormes), 5 Gi se acaban. El compactor borra cuando vencen los 7 días, no cuando el disco está lleno. Mitigación: monitorear con `kubectl exec -n observability loki-0 -- df -h /var/loki` y bumpear el PVC si hace falta. En cloud el storage es elástico, esto es solo un problema en local.
  - **Alloy depende de hostPath para leer `/var/log/pods`.** Eso lo obliga a correr con privilegios elevados (PSS `baseline`). Si el cluster tiene PodSecurity `restricted` enforced, Alloy no arranca. Mitigado en `manifests/namespace.yaml` aplicando `pod-security.kubernetes.io/enforce: baseline` solo a este namespace, sin tocar los demás.
  - **Versión LTS de los charts puede cambiar.** Dejamos los pins con un comentario "verificar la última con `helm search repo`". Para 2026 los pins indicados son seguros; en 2027+ revisar.

## Referencias

- Loki — arquitectura y deployment modes: <https://grafana.com/docs/loki/latest/get-started/deployment-modes/>
- LogQL spec: <https://grafana.com/docs/loki/latest/query/>
- Grafana Alloy (sucesor de Promtail/Grafana Agent): <https://grafana.com/docs/alloy/latest/>
- Promtail status (mantenimiento-only desde 2024): <https://grafana.com/docs/loki/latest/clients/promtail/>
- Comparativa Loki vs ELK: <https://grafana.com/blog/2020/12/08/how-to-create-fast-queries-with-loki/>
- python-json-logger: <https://github.com/madzak/python-json-logger>
- ADR 0003 (k8s Job + CronJob) — esta decisión extiende ese stack agregando la capa de observability sobre los Pods del CronJob.
- ADR 0007 (Postgres como StatefulSet) — comparte el mismo principio: cluster local autocontenido, sin cuentas de cloud, primitivas reales de Kubernetes.
- Kleppmann — *Designing Data-Intensive Applications*, cap. 3 (storage engines): el contraste entre indexar todo (ELK, Lucene) vs indexar solo metadata (Loki) es exactamente el mismo trade-off que hash index vs B-tree explicado allí.
