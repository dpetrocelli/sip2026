# Seminario de Integración Profesional 2026 — Material de Cátedra

Sitio estático con los Trabajos Prácticos del **Seminario de Integración Profesional**.
Universidad Nacional de Luján · Departamento de Ciencias Básicas · Cátedra Petrocelli.

🌐 **Sitio web**: https://dpetrocelli.github.io/sip2026/

## Trabajos Prácticos

| TP | Tema | Páginas |
|----|------|---------|
| TP 0 | Prerrequisitos: k3s + Kubernetes básico | [practica-0.html](practica-0.html) |
| TP 1 · Parte 1 | Selenium + MercadoLibre | [practica-1-parte-1.html](practica-1-parte-1.html) |
| TP 1 · Parte 2 | Robustez, Tests, Docker, k3s, CI/CD | [practica-1-parte-2.html](practica-1-parte-2.html) |
| TP 2 · Parte 1 | Loki + Promtail/Alloy + Grafana | [practica-2-parte-1.html](practica-2-parte-1.html) |
| TP 2 · Parte 2 | EFK (Elasticsearch + Fluent Bit + Kibana) | [practica-2-parte-2.html](practica-2-parte-2.html) |
| TP 2 · Parte 3 | OpenTelemetry: Collector + SDK + multi-backend | [practica-2-parte-3.html](practica-2-parte-3.html) |
| TP 2 · Parte 4 | Cierre: comparativa + ADR magisterial | [practica-2-parte-4.html](practica-2-parte-4.html) |

## Módulo Blockchain (4 clases · obligatorio)

El TPC del Seminario exige una **pasarela de pago basada en blockchain real (Sepolia testnet)** que vale **70% de la evaluación técnica**. Estas 4 clases cubren el camino corto y técnico para llegar.

| Clase | Tema | Página |
|---|---|---|
| Overview | Hub con 5 diagramas hero + roadmap | [blockchain-overview.html](blockchain-overview.html) |
| Clase 1 | Fundamentos + setup + tu primer contrato | [blockchain-clase-1.html](blockchain-clase-1.html) |
| Clase 2 | ERC-20 + PaymentGateway + Reentrancy | [blockchain-clase-2.html](blockchain-clase-2.html) |
| Clase 3 | Frontend + integración + onramp testnet | [blockchain-clase-3.html](blockchain-clase-3.html) |
| Clase 4 | NFTs gamificados + tokenomics + Slither | [blockchain-clase-4.html](blockchain-clase-4.html) |

**Repo de clase 1**: [github.com/dpetrocelli/sip2026-blockchain-clase1](https://github.com/dpetrocelli/sip2026-blockchain-clase1) (SimpleStorage scaffold).

## Estructura del repo

```
html-pages/
├── index.html               # Landing con cards por TP + módulo blockchain
├── template.html            # Template pandoc con branding UNLu/DCB
├── build.sh                 # Render MD → HTML
├── TP0.md, TP1.md, TP2.md, TP3-1..4.md   # Fuentes de los TPs legacy
├── blockchain-overview.md, blockchain-clase-{1..4}.md   # Fuentes blockchain
└── assets/
    ├── style.css
    ├── diagramas/           # PNG + .drawio de los 5 hero diagrams
    ├── unlu_escudo.png
    └── logo_dcb.png
```

## Build local

Requiere [pandoc](https://pandoc.org/) ≥ 3.0:

```bash
./build.sh
xdg-open index.html
```

---

UNLu · DCB · 2026 · Cátedra Petrocelli
