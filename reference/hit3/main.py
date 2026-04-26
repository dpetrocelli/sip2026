"""Hit #3 — Filtros DOM + screenshot.

Extiende el Hit #2 con:
- Aplicación de filtros vía DOM: Condición=Nuevo, Tienda Oficial=Sí,
  Ordenar=Más relevantes (clicks reales, no modificación de URL).
- Manejo del banner de cookies.
- Captura de screenshot a screenshots/<producto>_<browser>.png
"""

import argparse
import logging
import sys
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent.parent / "hit2"))
from browser_factory import create_driver  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from filters import apply_all_filters  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

ML_URL = "https://www.mercadolibre.com.ar"
SEARCH_QUERY = "bicicleta rodado 29"
MAX_TITLES = 5
TIMEOUT = 15

SEL_SEARCH_BOX = "input.nav-search-input"
SEL_RESULT_TITLES = "h2.ui-search-item__title"

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"


def parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos.

    Returns:
        Namespace con `browser` (str | None) y `product` (str).
    """
    parser = argparse.ArgumentParser(description="Scraper MercadoLibre — Hit #3")
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default=None,
        help="Browser a usar (default: env BROWSER o 'chrome').",
    )
    parser.add_argument(
        "--product",
        default=SEARCH_QUERY,
        help=f"Producto a buscar (default: '{SEARCH_QUERY}').",
    )
    return parser.parse_args()


def product_to_filename(product: str) -> str:
    """Convierte un nombre de producto a un nombre de archivo seguro.

    Args:
        product: Nombre del producto (ej: "bicicleta rodado 29").

    Returns:
        Slug del producto (ej: "bicicleta_rodado_29").
    """
    return product.lower().replace(" ", "_").replace("/", "_")


def take_screenshot(driver, product: str, browser: str) -> Path:
    """Captura un screenshot y lo guarda en screenshots/.

    Args:
        driver: WebDriver activo.
        product: Nombre del producto buscado.
        browser: Nombre del browser usado.

    Returns:
        Path al archivo de screenshot generado.
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = product_to_filename(product)
    filename = SCREENSHOTS_DIR / f"{slug}_{browser}.png"
    driver.save_screenshot(str(filename))
    logger.info("Screenshot guardado en: %s", filename)
    return filename


def search_product(driver, query: str) -> None:
    """Navega a ML y ejecuta la búsqueda.

    Args:
        driver: WebDriver activo.
        query: Término de búsqueda.
    """
    wait = WebDriverWait(driver, TIMEOUT)

    logger.info("Navegando a %s", ML_URL)
    driver.get(ML_URL)

    logger.info("Búsqueda: '%s'", query)
    search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_SEARCH_BOX)))
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    logger.info("Esperando resultados...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL_RESULT_TITLES)))


def get_titles(driver, max_results: int) -> list[str]:
    """Extrae los títulos visibles de la página de resultados actual.

    Args:
        driver: WebDriver activo en la página de resultados.
        max_results: Cantidad máxima de títulos a retornar.

    Returns:
        Lista de títulos.
    """
    elements = driver.find_elements(By.CSS_SELECTOR, SEL_RESULT_TITLES)
    return [el.text.strip() for el in elements if el.text.strip()][:max_results]


def main() -> None:
    """Punto de entrada principal del Hit #3."""
    args = parse_args()

    driver = create_driver(browser=args.browser)
    browser_name = driver.capabilities.get("browserName", "unknown")
    logger.info("Iniciando scraper en %s", browser_name)

    try:
        search_product(driver, args.product)

        # Aplicar filtros DOM
        filter_results = apply_all_filters(driver)
        logger.info("Estado de filtros: %s", filter_results)
        logger.info("URL final: %s", driver.current_url)

        # Capturar screenshot con filtros aplicados
        take_screenshot(driver, args.product, browser_name)

        # Mostrar títulos post-filtrado
        titles = get_titles(driver, MAX_TITLES)
        if not titles:
            logger.warning("No se encontraron títulos después de aplicar filtros.")
            sys.exit(1)

        for i, title in enumerate(titles, start=1):
            print(f"{i}. {title}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
