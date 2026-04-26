"""Módulo de filtros DOM para MercadoLibre — Hit #4.

Aplica los filtros de Condición=Nuevo, Tienda Oficial=Sí y
Ordenar=Más relevantes navegando el DOM (clicks reales, no URL).

Diseño:
- Cada filtro tiene su propia función; si el filtro ya está aplicado
  o no está disponible, se loguea y se continúa sin romper.
- El banner de cookies se maneja antes de aplicar cualquier filtro.
"""

import logging

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

TIMEOUT = 15

# ──────────────────────────────────────────────
# Selectores de filtros (centralizados aquí)
# ──────────────────────────────────────────────

# Banner de cookies
SEL_COOKIE_BANNER = "button#newCookieBanner, button[data-testid='action:understood-button'], button.cookie-consent-banner-opt-in"
SEL_COOKIE_ACCEPT = (
    "button#newCookieBanner, "
    "button[data-testid='action:understood-button'], "
    "button.cookie-consent-banner-opt-in, "
    "[class*='cookie'] button, "
    "button[class*='cookie']"
)

# Filtro Condición → Nuevo
# ML muestra los filtros como links con texto dentro de spans
SEL_FILTER_NUEVO_LINK = (
    "//span[normalize-space(text())='Nuevo']/ancestor::a | "
    "//a[normalize-space(text())='Nuevo'] | "
    "//li[contains(@class,'ui-search-filter')]//span[text()='Nuevo']/parent::a"
)

# Filtro Tienda Oficial → Sí
SEL_FILTER_TIENDA_LINK = (
    "//span[normalize-space(text())='Sí']/ancestor::a[1] | "
    "//a[normalize-space(text())='Sí'] | "
    "//li[contains(@class,'ui-search-filter')]//span[text()='Sí']/parent::a"
)

# Ordenar → Más relevantes (texto puede variar, probamos variantes)
SEL_SORT_BUTTON = "button.andes-dropdown__trigger, [class*='ui-search-sort'] button, [class*='sort-filter'] button"
SEL_SORT_RELEVANCE = (
    "//li[contains(@class,'andes-list__item')]//span[contains(text(),'relevante')] | "
    "//li[contains(@class,'andes-dropdown')]//span[contains(text(),'relevante')]"
)


def _safe_click(driver, element) -> None:
    """Intenta click normal; si está interceptado, usa JavaScript.

    Args:
        driver: WebDriver activo.
        element: WebElement a clickear.
    """
    try:
        element.click()
    except ElementClickInterceptedException:
        logger.debug("Click interceptado, usando JS click")
        driver.execute_script("arguments[0].click();", element)


def dismiss_cookie_banner(driver) -> None:
    """Cierra el banner de cookies si aparece.

    No falla si el banner no está presente.

    Args:
        driver: WebDriver activo.
    """
    try:
        wait = WebDriverWait(driver, 5)
        # Intenta varios selectores posibles del banner
        selectors = [
            (By.CSS_SELECTOR, "button#newCookieBanner"),
            (By.CSS_SELECTOR, "button[data-testid='action:understood-button']"),
            (By.CSS_SELECTOR, "button.cookie-consent-banner-opt-in"),
            (By.XPATH, "//button[contains(text(),'Entendido')]"),
            (By.XPATH, "//button[contains(text(),'Acepto')]"),
            (By.XPATH, "//button[contains(text(),'Aceptar')]"),
        ]
        for by, selector in selectors:
            try:
                btn = wait.until(EC.element_to_be_clickable((by, selector)))
                _safe_click(driver, btn)
                logger.info("Banner de cookies cerrado")
                return
            except TimeoutException:
                continue
        logger.debug("No se encontró banner de cookies")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Error al cerrar banner de cookies: %s", exc)


def apply_filter_nuevo(driver) -> bool:
    """Aplica el filtro Condición=Nuevo.

    Args:
        driver: WebDriver activo (debe estar en la página de resultados).

    Returns:
        True si el filtro se aplicó, False si no estaba disponible.
    """
    wait = WebDriverWait(driver, TIMEOUT)
    try:
        link = wait.until(EC.element_to_be_clickable((By.XPATH, SEL_FILTER_NUEVO_LINK)))
        _safe_click(driver, link)
        # Esperar que la URL cambie o los resultados se recarguen
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.ui-search-item__title")))
        logger.info("Filtro 'Nuevo' aplicado")
        return True
    except TimeoutException:
        logger.warning("Filtro 'Nuevo' no disponible en esta búsqueda")
        return False
    except NoSuchElementException:
        logger.warning("Filtro 'Nuevo' no encontrado en el DOM")
        return False


def apply_filter_tienda_oficial(driver) -> bool:
    """Aplica el filtro Tienda Oficial=Sí.

    Args:
        driver: WebDriver activo (debe tener el filtro Nuevo ya aplicado).

    Returns:
        True si el filtro se aplicó, False si no estaba disponible.
    """
    wait = WebDriverWait(driver, TIMEOUT)
    try:
        # Buscar link con texto "Sí" dentro de la sección de Tienda Oficial
        # La estructura de ML tiene el filtro en un panel lateral
        link = wait.until(EC.element_to_be_clickable((By.XPATH, SEL_FILTER_TIENDA_LINK)))
        _safe_click(driver, link)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.ui-search-item__title")))
        logger.info("Filtro 'Tienda Oficial' aplicado")
        return True
    except TimeoutException:
        logger.warning("Filtro 'Tienda Oficial' no disponible en esta búsqueda")
        return False
    except NoSuchElementException:
        logger.warning("Filtro 'Tienda Oficial' no encontrado en el DOM")
        return False


def apply_sort_relevance(driver) -> bool:
    """Aplica el ordenamiento por Más relevantes.

    Args:
        driver: WebDriver activo.

    Returns:
        True si se aplicó, False si no estaba disponible.
    """
    wait = WebDriverWait(driver, TIMEOUT)
    try:
        # Abrir el dropdown de ordenamiento
        sort_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_SORT_BUTTON)))
        _safe_click(driver, sort_btn)

        # Seleccionar "Más relevantes" del dropdown
        option = wait.until(EC.element_to_be_clickable((By.XPATH, SEL_SORT_RELEVANCE)))
        _safe_click(driver, option)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.ui-search-item__title")))
        logger.info("Ordenamiento 'Más relevantes' aplicado")
        return True
    except TimeoutException:
        logger.warning("Opción 'Más relevantes' no disponible")
        return False


def apply_all_filters(driver) -> dict[str, bool]:
    """Aplica todos los filtros en orden y retorna el estado de cada uno.

    Orden: cookies → Nuevo → Tienda Oficial → Más relevantes.
    Cada filtro es independiente: si uno falla, los siguientes se intentan igual.

    Args:
        driver: WebDriver activo en la página de resultados de ML.

    Returns:
        Diccionario con el resultado de cada filtro aplicado.
    """
    dismiss_cookie_banner(driver)

    results = {
        "nuevo": apply_filter_nuevo(driver),
        "tienda_oficial": apply_filter_tienda_oficial(driver),
        "mas_relevantes": apply_sort_relevance(driver),
    }

    applied = [k for k, v in results.items() if v]
    skipped = [k for k, v in results.items() if not v]
    if applied:
        logger.info("Filtros aplicados: %s", applied)
    if skipped:
        logger.warning("Filtros no disponibles: %s", skipped)

    return results
