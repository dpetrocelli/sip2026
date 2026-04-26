# Hit #6 — Tests automatizados + cobertura ≥ 70 %

Tests unitarios y de integración del scraper, con gate de cobertura validado por CI.

> Las **piezas testables** del scraper (extractors, selectores, retries) están cubiertas con mocks/fakes — los tests **no abren browser real ni hacen requests a MercadoLibre**. Esto los hace rápidos (<1s todo el suite), determinísticos y CI-friendly.

## Suite

| Archivo | Qué cubre |
|---------|-----------|
| [`tests/conftest.py`](../tests/conftest.py) | Fixtures comunes (mock de `WebElement`, fake driver) |
| [`tests/test_extractors.py`](../tests/test_extractors.py) | Los 6 extractors del Hit #4 (titulo, precio, link, tienda_oficial, envio_gratis, cuotas_sin_interes), happy path + soft-fail a `null` cuando el campo no está |
| [`tests/test_retry.py`](../tests/test_retry.py) | Decorador `@with_backoff`: éxito al 1er intento, éxito tras N fallos, fallo total tras max_attempts, excepción no-retryable se propaga sin reintento |
| [`tests/test_browser_factory.py`](../tests/test_browser_factory.py) | Cadena de resolución del browser (CLI > env > default), validación de browser no soportado, detección de modo headless |
| [`tests/test_ml_selectors.py`](../tests/test_ml_selectors.py) | Sanity: las constantes esperadas existen y son strings no vacíos |

## Cobertura — exclusiones razonadas

`pyproject.toml` configura `[tool.coverage.run]` para excluir 3 módulos del cálculo de cobertura:

| Módulo | Por qué se excluye |
|--------|--------------------|
| `hit5/main.py` | Glue code — orquesta browser real + ML. No hay forma honesta de cubrirlo sin un E2E completo |
| `hit5/filters.py` | Cada función llama al DOM real de ML. Mockear todos los `find_element` no aporta valor — el contrato real está en E2E |
| `hit5/browser_factory.py` | Construir un driver Chrome/Firefox real es lo único que valida que la factory funciona. La parte testeable (`_is_headless`, validación de browser) sí está cubierta vía tests indirectos |

Resultado: **cobertura efectiva 97 % sobre el código testable** (`extractors.py`, `ml_selectors.py`, `retry.py`).

## Cómo correr local

```bash
# Setup venv (una vez)
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov

# Correr todo el suite con coverage gate
pytest

# Solo unos tests
pytest tests/test_retry.py -v

# Coverage HTML detallada
pytest && open htmlcov/index.html
```

El gate de `--cov-fail-under=70` está **hardcoded en `pyproject.toml`** — si la cobertura cae bajo 70 %, `pytest` retorna no-cero y CI falla.

## Output local de la última corrida (referencia)

```
77 passed in 0.15s
================================ tests coverage ================================
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
hit5/extractors.py        52      0   100%
hit5/ml_selectors.py      13      0   100%
hit5/retry.py             30      3    90%   78-80
----------------------------------------------------
TOTAL                     95      3    97%
Required test coverage of 70% reached. Total coverage: 96.84%
```

## Conexión con CI

[`.github/workflows/scrape.yml`](../.github/workflows/scrape.yml) corre `pytest` (con cobertura) en el job `unit-tests`. Si falla el gate, el pipeline corta y NO se ejecutan los tests de integración ni el deploy.

## Pre-commit local

[`.pre-commit-config.yaml`](../.pre-commit-config.yaml) corre `gitleaks` + `ruff check` + `ruff format` antes de cada commit. Activación:

```bash
pip install pre-commit
pre-commit install
```
