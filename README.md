# Seminario de Integración Profesional 2026 — Material de Cátedra

Sitio estático con los Trabajos Prácticos del **Seminario de Integración Profesional**.
Universidad Nacional de Luján · Departamento de Ciencias Básicas · Cátedra Petrocelli.

## Estructura

```
html-pages/
├── index.html               # Landing con cards por TP
├── template.html            # Template pandoc con branding UNLu/DCB
├── build.sh                 # Render MD → HTML
├── TP1.md                   # Fuente del TP1 (Selenium + MercadoLibre)
├── practica-1.html          # TP1 renderizado
└── assets/
    ├── style.css
    ├── unlu_escudo.png
    ├── logo_dcb.png
    └── images/
```

## Build

Requiere [pandoc](https://pandoc.org/) ≥ 3.0:

```bash
./build.sh
xdg-open index.html
```

## Trabajos Prácticos

| TP | Tema | Entrega |
|----|------|---------|
| TP 1 | Automatización Web con Selenium — MercadoLibre multi-browser | a definir |

---

UNLu · DCB · 2026
