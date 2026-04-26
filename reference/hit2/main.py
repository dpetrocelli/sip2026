"""Hit #2 — Browser Factory + soporte CLI/env para Chrome y Firefox.

Extiende el Hit #1 con:
- Browser Factory en browser_factory.py
- Resolución del browser: CLI > env > default("chrome")
- Funciona idéntico en Chrome y Firefox
"""

import argparse
import logging
import os as _os
import sys

# Importamos la factory del mismo paquete
import sys as _sys

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_sys.path.insert(0, _os.path.dirname(__file__))
from browser_factory import create_driver  # noqa: E402

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


def parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos.

    Returns:
        Namespace con el campo `browser` (str | None).
    """
    parser = argparse.ArgumentParser(description="Scraper MercadoLibre — Hit #2")
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default=None,
        help="Browser a usar. Si no se pasa, se lee BROWSER env var (default: chrome).",
    )
    return parser.parse_args()


def search_and_get_titles(driver, query: str, max_results: int) -> list[str]:
    """Navega a ML, ejecuta la búsqueda y retorna títulos.

    Args:
        driver: Instancia activa de WebDriver (Chrome o Firefox).
        query: Término de búsqueda.
        max_results: Cantidad máxima de títulos a retornar.

    Returns:
        Lista de títulos, hasta max_results elementos.
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

    title_elements = driver.find_elements(By.CSS_SELECTOR, SEL_RESULT_TITLES)
    titles = [el.text.strip() for el in title_elements if el.text.strip()]
    return titles[:max_results]


def main() -> None:
    """Punto de entrada principal del Hit #2."""
    args = parse_args()

    # Cadena de resolución: CLI > env > default (manejado dentro de create_driver)
    driver = create_driver(browser=args.browser)
    browser_name = driver.capabilities.get("browserName", "unknown")
    logger.info("Iniciando scraper en %s", browser_name)

    try:
        titles = search_and_get_titles(driver, SEARCH_QUERY, MAX_TITLES)
        if not titles:
            logger.warning("No se encontraron títulos.")
            sys.exit(1)
        for i, title in enumerate(titles, start=1):
            print(f"{i}. {title}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
