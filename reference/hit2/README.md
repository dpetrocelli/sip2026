# Hit #2 — Browser Factory

## Qué agrega respecto al Hit #1

- Módulo `browser_factory.py` con `create_driver(browser)` que encapsula
  la creación de Chrome y Firefox con configuración uniforme.
- Cadena de resolución del browser: **CLI > env var `BROWSER` > default "chrome"**.
- Mismo output y comportamiento en ambos browsers.

## Cómo ejecutar

```bash
# Chrome (default)
python hit2/main.py

# Firefox via env var
BROWSER=firefox python hit2/main.py

# Firefox via CLI
python hit2/main.py --browser firefox

# Headless
HEADLESS=true BROWSER=chrome python hit2/main.py
```

## Estructura

```
hit2/
├── README.md
├── browser_factory.py   ← encapsula Chrome y Firefox
└── main.py              ← lógica de scraping (igual al Hit #1)
```

## Diferencias Chrome vs Firefox observadas

| Aspecto | Chrome | Firefox |
|---------|--------|---------|
| Tiempo de carga inicial | ~2s | ~3s |
| Anti-detección | CDP `Page.addScriptToEvaluateOnNewDocument` | `dom.webdriver.enabled = false` via preferences |
| Selectores CSS | Idénticos | Idénticos |
| Headless flag | `--headless=new` | `--headless` (modo legacy) |

## Decisiones de diseño

- La factory resuelve `browser` con la cadena CLI > env > default para que
  el mismo script sirva en local, CI y Docker sin cambiar código.
- Firefox usa `options.set_preference` en lugar de CDP porque geckodriver
  no expone el protocolo CDP completo.
