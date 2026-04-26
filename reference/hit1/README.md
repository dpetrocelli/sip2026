# Hit #1 — Setup, búsqueda y lectura de títulos

## Qué hace

Abre Chrome, navega a `mercadolibre.com.ar`, busca `bicicleta rodado 29` y
imprime por consola los títulos de los primeros 5 resultados.

## Qué introduce este Hit

- Configuración del proyecto con `selenium` 4.x y Selenium Manager (sin
  `webdriver-manager` separado — el manager viene integrado desde selenium 4.6).
- **`WebDriverWait` + `expected_conditions`** para toda sincronización. Cero `time.sleep`.
- User-Agent custom para evitar el empty-state que ML devuelve en headless.
- Ocultamiento de `navigator.webdriver` via CDP para evadir detección básica.

## Cómo ejecutar

```bash
# Desde la raíz del proyecto
pip install -r requirements.txt

# Headed (ventana visible)
python hit1/main.py

# Headless
HEADLESS=true python hit1/main.py
```

O como módulo desde la raíz:

```bash
python -m hit1.main
```

## Output esperado

```
[INFO] Iniciando scraper en chrome
[INFO] Navegando a https://www.mercadolibre.com.ar
[INFO] Búsqueda: 'bicicleta rodado 29'
[INFO] Esperando resultados...
1. Bicicleta Mountain Bike Rodado 29 21 Velocidades ...
2. Bicicleta Mtb Rodado 29 Aluminio Shimano 21v ...
3. ...
```

## Decisiones de diseño

| Decisión | Razón |
|----------|-------|
| Selenium Manager (integrado) | Evita dependencia extra de `webdriver-manager`; selenium >= 4.6 lo incluye |
| User-Agent de Chrome 120 | ML devuelve HTML vacío si detecta headless sin UA real |
| `--disable-blink-features=AutomationControlled` | Evita que ML detecte el browser como automatizado |
| `SEL_RESULT_TITLES = "h2.ui-search-item__title"` | Selector semántico estable; no depende de clases con hash autogenerado |
