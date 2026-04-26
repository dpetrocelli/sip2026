"""Hit #5 — Robustez: retries con backoff, selectores centralizados, logging.

Mejoras respecto al Hit #4:
- Selectores en módulo aparte (`selectors.py`).
- Reintentos con backoff exponencial ante fallos transitorios (`retry.py`).
- Logging estructurado a archivo (`logs/scraper.log`) y stdout.
- Cada producto se aísla: si uno falla por timeout fatal después de 3 retries,
  se registra y se continúa con los siguientes.
"""

import argparse
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent))
from browser_factory import create_driver  # noqa: E402
from extractors import extract_result  # noqa: E402
from filters import apply_all_filters  # noqa: E402
from ml_selectors import RESULT_CARD_CSS, SEARCH_BOX_CSS  # noqa: E402
from retry import with_backoff  # noqa: E402

# ──────────────────────────────────────────────
# Configuración de logging
# ──────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "scraper.log"

_root = logging.getLogger()
_root.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")

_stdout = logging.StreamHandler(sys.stdout)
_stdout.setFormatter(_fmt)
_root.addHandler(_stdout)

_file = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3)
_file.setFormatter(_fmt)
_root.addHandler(_file)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constantes del scraper
# ──────────────────────────────────────────────

ML_URL = "https://www.mercadolibre.com.ar"
TIMEOUT = 20
RESULTS_PER_PRODUCT = 10

PRODUCTS = [
    "bicicleta rodado 29",
    "iPhone 16 Pro Max",
    "GeForce RTX 5090",
]

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Mapping explícito producto → filename (la consigna pide geforce_5090, no geforce_rtx_5090)
PRODUCT_FILENAMES = {
    "bicicleta rodado 29": "bicicleta_rodado_29",
    "iPhone 16 Pro Max": "iphone_16_pro_max",
    "GeForce RTX 5090": "geforce_5090",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper MercadoLibre — Hit #5")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default=None)
    parser.add_argument("--products", nargs="+", default=PRODUCTS)
    parser.add_argument("--limit", type=int, default=RESULTS_PER_PRODUCT)
    return parser.parse_args()


def slugify(product: str) -> str:
    if product in PRODUCT_FILENAMES:
        return PRODUCT_FILENAMES[product]
    return product.lower().replace(" ", "_").replace("/", "_")


@with_backoff(max_attempts=3, base_delay=2.0)
def search_and_filter(driver, query: str) -> None:
    """Navega a ML, busca, aplica filtros. Reintenta hasta 3 veces."""
    wait = WebDriverWait(driver, TIMEOUT)
    driver.get(ML_URL)
    box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_BOX_CSS)))
    box.clear()
    box.send_keys(query)
    box.send_keys(Keys.RETURN)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RESULT_CARD_CSS)))
    apply_all_filters(driver)


def collect_results(driver, limit: int) -> list[dict]:
    """Extrae hasta `limit` resultados únicos de la página actual.

    Dedup por link (clave estable); fallback a titulo si link es null.
    Ignora cards que solo tienen título sin precio (anuncios sponsoreados).
    """
    cards = driver.find_elements(By.CSS_SELECTOR, RESULT_CARD_CSS)
    out = []
    seen_keys = set()
    for card in cards:
        if len(out) >= limit:
            break
        try:
            data = extract_result(card)
            if not data["titulo"]:
                continue
            key = data["link"] or data["titulo"]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error extrayendo card: %s", exc)
    return out


def scrape_product(driver, query: str, limit: int) -> list[dict]:
    """Scrapea un producto. Si falla después de retries, devuelve []."""
    logger.info("=== Producto: '%s' ===", query)
    try:
        search_and_filter(driver, query)
        results = collect_results(driver, limit)
        logger.info("'%s' → %d resultados", query, len(results))
        return results
    except Exception as exc:  # noqa: BLE001
        logger.error("Producto '%s' falló definitivamente: %s", query, exc)
        return []


def write_json(product: str, results: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{slugify(product)}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("JSON escrito: %s (%d registros)", path, len(results))
    return path


def main() -> None:
    args = parse_args()
    driver = create_driver(browser=args.browser)
    browser_name = driver.capabilities.get("browserName", "unknown")
    logger.info("Iniciando scraper en %s (logs en %s)", browser_name, LOG_FILE)

    try:
        for product in args.products:
            results = scrape_product(driver, product, args.limit)
            write_json(product, results)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
