"""Hit #4 — Extracción estructurada a JSON de los 3 productos.

Itera los 3 productos del enunciado, extrae 10 resultados por cada uno
con todos los campos requeridos, y guarda un JSON por producto en `output/`.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent.parent / "hit2"))
from browser_factory import create_driver  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from extractors import extract_result  # noqa: E402
from filters import apply_all_filters  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

ML_URL = "https://www.mercadolibre.com.ar"
TIMEOUT = 20
RESULTS_PER_PRODUCT = 10

PRODUCTS = [
    "bicicleta rodado 29",
    "iPhone 16 Pro Max",
    "GeForce RTX 5090",
]

OUTPUT_DIR = Path(__file__).parent.parent / "output"

SEL_SEARCH_BOX = "input.nav-search-input"
SEL_RESULT_CARDS = "li.ui-search-layout__item, div.ui-search-result__wrapper"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper MercadoLibre — Hit #4")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default=None)
    parser.add_argument(
        "--products",
        nargs="+",
        default=PRODUCTS,
        help="Lista de productos a buscar (default: los 3 del TP).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=RESULTS_PER_PRODUCT,
        help=f"Resultados por producto (default: {RESULTS_PER_PRODUCT}).",
    )
    return parser.parse_args()


def slugify(product: str) -> str:
    return product.lower().replace(" ", "_").replace("/", "_")


def search_and_filter(driver, query: str) -> None:
    """Navega a ML, busca el producto y aplica los filtros."""
    wait = WebDriverWait(driver, TIMEOUT)
    driver.get(ML_URL)
    box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_SEARCH_BOX)))
    box.clear()
    box.send_keys(query)
    box.send_keys(Keys.RETURN)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL_RESULT_CARDS)))
    apply_all_filters(driver)


def collect_results(driver, limit: int) -> list[dict]:
    """Extrae hasta `limit` resultados de la página actual."""
    cards = driver.find_elements(By.CSS_SELECTOR, SEL_RESULT_CARDS)
    results = []
    for card in cards[:limit]:
        data = extract_result(card)
        if data["titulo"]:
            results.append(data)
    return results


def scrape_product(driver, query: str, limit: int) -> list[dict]:
    """Scrapea un producto end-to-end y devuelve los resultados extraídos."""
    logger.info("=== Scraping: '%s' ===", query)
    try:
        search_and_filter(driver, query)
        results = collect_results(driver, limit)
        logger.info("'%s' → %d resultados", query, len(results))
        return results
    except TimeoutException as exc:
        logger.error("Timeout scrapeando '%s': %s", query, exc)
        return []


def write_json(product: str, results: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{slugify(product)}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("JSON escrito: %s", path)
    return path


def main() -> None:
    args = parse_args()
    driver = create_driver(browser=args.browser)
    browser_name = driver.capabilities.get("browserName", "unknown")
    logger.info("Iniciando scraper en %s", browser_name)

    try:
        for product in args.products:
            results = scrape_product(driver, product, args.limit)
            write_json(product, results)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
