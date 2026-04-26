"""Fixtures compartidas para los tests del TP Selenium MercadoLibre — SIP 2026.

Provee mocks de WebElement y WebDriver sin necesidad de un browser real.
"""

from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import NoSuchElementException

# ──────────────────────────────────────────────
# Helpers para construir fake WebElements
# ──────────────────────────────────────────────


def make_element(text: str = "", href: str | None = None) -> MagicMock:
    """Construye un MagicMock que simula un WebElement con texto y atributo href.

    Args:
        text: Texto que devuelve `.text`.
        href: Valor del atributo "href". None si el atributo no existe.

    Returns:
        MagicMock configurado como WebElement.
    """
    elem = MagicMock()
    elem.text = text
    elem.get_attribute.side_effect = lambda attr: href if attr == "href" else None
    return elem


def make_card(
    title: str | None = "Bicicleta Rodado 29",
    price: str | None = "250.000",
    href: str | None = "https://articulo.mercadolibre.com.ar/MLA-123",
    official_store: str | None = None,
    free_shipping: str | None = None,
    installments: str | None = None,
) -> MagicMock:
    """Construye un MagicMock de la card de resultado de ML.

    Cada campo puede ser None para simular que no aparece en el DOM
    (en ese caso, find_element lanza NoSuchElementException).

    Args:
        title: Texto del título. None → NoSuchElementException.
        price: Texto de la fracción del precio. None → NoSuchElementException.
        href: URL del link. None → NoSuchElementException.
        official_store: Texto de tienda oficial. None → NoSuchElementException.
        free_shipping: Texto del envío. None → NoSuchElementException.
        installments: Texto de cuotas. None → NoSuchElementException.

    Returns:
        MagicMock configurado como card WebElement.
    """
    from hit5.extractors import (
        SEL_FREE_SHIPPING,
        SEL_INSTALLMENTS,
        SEL_LINK,
        SEL_OFFICIAL_STORE,
        SEL_PRICE_FRACTION,
        SEL_TITLE,
    )

    # Mapa selector → elemento o excepción
    selector_map: dict[str, MagicMock | None] = {
        SEL_TITLE: make_element(title) if title is not None else None,
        SEL_PRICE_FRACTION: make_element(price) if price is not None else None,
        SEL_LINK: make_element(href=href) if href is not None else None,
        SEL_OFFICIAL_STORE: make_element(official_store) if official_store is not None else None,
        SEL_FREE_SHIPPING: make_element(free_shipping) if free_shipping is not None else None,
        SEL_INSTALLMENTS: make_element(installments) if installments is not None else None,
    }

    def _find(by, selector):  # noqa: ANN001
        elem = selector_map.get(selector)
        if elem is None:
            raise NoSuchElementException(f"No element: {selector}")
        return elem

    card = MagicMock()
    card.find_element.side_effect = _find
    return card


# ──────────────────────────────────────────────
# Fixtures de pytest
# ──────────────────────────────────────────────


@pytest.fixture
def full_card() -> MagicMock:
    """Card con todos los campos presentes."""
    return make_card(
        title="Bicicleta Rodado 29 MTB",
        price="250.000",
        href="https://articulo.mercadolibre.com.ar/MLA-123",
        official_store="Trek Store",
        free_shipping="Llega gratis",
        installments="12x sin interés",
    )


@pytest.fixture
def empty_card() -> MagicMock:
    """Card sin ningún campo (todos lanzan NoSuchElementException)."""
    return make_card(
        title=None,
        price=None,
        href=None,
        official_store=None,
        free_shipping=None,
        installments=None,
    )


@pytest.fixture
def fake_driver() -> MagicMock:
    """Fake WebDriver con métodos básicos mockeados."""
    driver = MagicMock()
    driver.capabilities = {"browserName": "chrome"}
    driver.current_url = "https://www.mercadolibre.com.ar"
    driver.find_elements.return_value = []
    return driver
