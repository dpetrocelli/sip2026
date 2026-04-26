"""Extractores de campos por resultado — Hit #4.

Cada función toma un WebElement (la "card" de un resultado) y devuelve el
campo correspondiente. Los campos opcionales devuelven None si no aparecen
en el DOM, sin romper la ejecución.

Diseño: cada extractor maneja sus propias excepciones, falla soft a None,
y registra el problema en debug log para investigación posterior.
"""

import logging
import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

# Selectores por campo dentro de una card de resultado
SEL_TITLE = "h2.ui-search-item__title, h2.poly-component__title, a.poly-component__title"
SEL_PRICE_FRACTION = "span.andes-money-amount__fraction"
SEL_LINK = "a.ui-search-link, a.poly-component__title-wrapper, h2 a"
SEL_OFFICIAL_STORE = (
    "span.poly-component__official, "
    "span.ui-search-official-store-label, "
    "span[class*='official-store']"
)
SEL_FREE_SHIPPING = "p.ui-search-item__shipping, p[class*='shipping'], span[class*='shipping']"
SEL_INSTALLMENTS = "span.ui-search-installments, span[class*='installments']"


def extract_titulo(card) -> str | None:
    """Extrae el título del producto."""
    try:
        return card.find_element(By.CSS_SELECTOR, SEL_TITLE).text.strip() or None
    except NoSuchElementException:
        logger.debug("Sin título en la card")
        return None


def extract_precio(card) -> float | None:
    """Extrae el precio numérico en ARS (sin símbolo `$` ni separadores)."""
    try:
        raw = card.find_element(By.CSS_SELECTOR, SEL_PRICE_FRACTION).text
        cleaned = re.sub(r"[^\d]", "", raw)
        return float(cleaned) if cleaned else None
    except NoSuchElementException:
        logger.debug("Sin precio en la card")
        return None


def extract_link(card) -> str | None:
    """Extrae el link absoluto al detalle del producto."""
    try:
        href = card.find_element(By.CSS_SELECTOR, SEL_LINK).get_attribute("href")
        return href if href and href.startswith("http") else None
    except NoSuchElementException:
        logger.debug("Sin link en la card")
        return None


def extract_tienda_oficial(card) -> str | None:
    """Extrae el nombre de la tienda oficial si aparece, sino None."""
    try:
        text = card.find_element(By.CSS_SELECTOR, SEL_OFFICIAL_STORE).text.strip()
        return text or None
    except NoSuchElementException:
        return None


def extract_envio_gratis(card) -> bool:
    """Detecta si la card promociona envío gratis."""
    try:
        text = card.find_element(By.CSS_SELECTOR, SEL_FREE_SHIPPING).text.lower()
        return "gratis" in text or "free" in text
    except NoSuchElementException:
        return False


def extract_cuotas_sin_interes(card) -> str | None:
    """Extrae el string de cuotas sin interés si aparece."""
    try:
        text = card.find_element(By.CSS_SELECTOR, SEL_INSTALLMENTS).text.strip()
        return text or None
    except NoSuchElementException:
        return None


def extract_result(card) -> dict:
    """Extrae todos los campos requeridos de una card.

    Args:
        card: WebElement de la card del resultado.

    Returns:
        Dict con los 6 campos del schema del Hit #4.
    """
    return {
        "titulo": extract_titulo(card),
        "precio": extract_precio(card),
        "link": extract_link(card),
        "tienda_oficial": extract_tienda_oficial(card),
        "envio_gratis": extract_envio_gratis(card),
        "cuotas_sin_interes": extract_cuotas_sin_interes(card),
    }
