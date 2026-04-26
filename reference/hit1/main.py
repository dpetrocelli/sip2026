"""Hit #1 — Scraper básico de MercadoLibre en Chrome.

Abre Chrome, navega a mercadolibre.com.ar, busca "bicicleta rodado 29"
y muestra por consola los títulos de los primeros 5 resultados.

Restricciones:
- Usa WebDriverWait + expected_conditions (cero time.sleep en scraping).
- User-Agent custom para evitar empty-state en modo headless.
"""

import logging
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
ML_URL = "https://www.mercadolibre.com.ar"
SEARCH_QUERY = "bicicleta rodado 29"
MAX_TITLES = 5
TIMEOUT = 15  # segundos para WebDriverWait

# User-Agent real de Chrome 120 en Linux.
# Sin esto, ML devuelve empty-state en headless.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Selectores estables de ML (estructura semántica, no clases autogeneradas)
SEL_SEARCH_BOX = "input.nav-search-input"
SEL_RESULT_TITLES = "h2.ui-search-item__title"


def build_chrome_driver() -> webdriver.Chrome:
    """Construye y retorna un WebDriver de Chrome configurado.

    Usa Selenium Manager (incluido en selenium>=4.6) para gestionar
    el chromedriver automáticamente — sin webdriver-manager extra.

    Returns:
        Instancia de WebDriver lista para usar.
    """
    options = Options()

    # Modo headless si la variable de entorno lo indica
    if os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes"):
        options.add_argument("--headless=new")
        logger.info("Modo headless activado")

    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Selenium Manager descarga chromedriver si hace falta
    driver = webdriver.Chrome(options=options)
    # Oculta la propiedad navigator.webdriver para evadir detección
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def search_and_get_titles(driver: webdriver.Chrome, query: str, max_results: int) -> list[str]:
    """Navega a ML, ejecuta la búsqueda y retorna los títulos encontrados.

    Args:
        driver: Instancia activa de WebDriver.
        query: Término de búsqueda.
        max_results: Cantidad máxima de títulos a retornar.

    Returns:
        Lista de títulos (strings), con hasta max_results elementos.
    """
    wait = WebDriverWait(driver, TIMEOUT)

    logger.info("Navegando a %s", ML_URL)
    driver.get(ML_URL)

    # Esperar a que el campo de búsqueda esté disponible para escribir
    logger.info("Búsqueda: '%s'", query)
    search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_SEARCH_BOX)))
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    # Esperar al menos un resultado antes de leer
    logger.info("Esperando resultados...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL_RESULT_TITLES)))

    title_elements = driver.find_elements(By.CSS_SELECTOR, SEL_RESULT_TITLES)
    titles = [el.text.strip() for el in title_elements if el.text.strip()]
    return titles[:max_results]


def main() -> None:
    """Punto de entrada principal del Hit #1."""
    logger.info("Iniciando scraper en chrome")

    driver = build_chrome_driver()
    try:
        titles = search_and_get_titles(driver, SEARCH_QUERY, MAX_TITLES)
        if not titles:
            logger.warning("No se encontraron títulos. ML puede haber detectado el bot.")
            sys.exit(1)
        for i, title in enumerate(titles, start=1):
            print(f"{i}. {title}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
