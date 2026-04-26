"""Browser Factory — Hit #3.

Crea instancias de WebDriver para Chrome o Firefox con configuración
uniforme: User-Agent custom, headless opcional, sin automation flags.

Cadena de resolución del browser:
    1. Argumento explícito a `create_driver(browser=...)`
    2. Variable de entorno `BROWSER`
    3. Default: "chrome"
"""

import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = logging.getLogger(__name__)

# User-Agent que evita el empty-state de ML en headless
_CHROME_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_FIREFOX_UA = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"

SUPPORTED_BROWSERS = ("chrome", "firefox")


def _is_headless() -> bool:
    """Retorna True si la variable de entorno HEADLESS está activa."""
    return os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")


def _build_chrome() -> webdriver.Chrome:
    """Construye un WebDriver de Chrome con opciones anti-detección."""
    options = ChromeOptions()
    if _is_headless():
        options.add_argument("--headless=new")
    options.add_argument(f"--user-agent={_CHROME_UA}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def _build_firefox() -> webdriver.Firefox:
    """Construye un WebDriver de Firefox con opciones anti-detección."""
    options = FirefoxOptions()
    if _is_headless():
        options.add_argument("--headless")
    options.set_preference("general.useragent.override", _FIREFOX_UA)
    # Deshabilita la flag de webdriver en Firefox
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    driver = webdriver.Firefox(options=options)
    return driver


def create_driver(browser: str | None = None) -> webdriver.Remote:
    """Crea y retorna un WebDriver según el browser indicado.

    Cadena de resolución:
        1. Parámetro `browser` (si se pasa explícitamente).
        2. Variable de entorno `BROWSER`.
        3. Default "chrome".

    Args:
        browser: Nombre del browser ("chrome" o "firefox"). Si es None,
                 se usa la cadena de resolución completa.

    Returns:
        Instancia de WebDriver lista para usar.

    Raises:
        ValueError: Si el browser no es soportado.
    """
    resolved = browser or os.getenv("BROWSER", "chrome")
    resolved = resolved.lower().strip()

    if resolved not in SUPPORTED_BROWSERS:
        raise ValueError(f"Browser '{resolved}' no soportado. Opciones: {SUPPORTED_BROWSERS}")

    logger.info("Iniciando browser: %s (headless=%s)", resolved, _is_headless())

    if resolved == "chrome":
        return _build_chrome()
    return _build_firefox()
