"""Sanity tests de las constantes de selectores — hit5/ml_selectors.py.

Valida que todas las constantes públicas esperadas existen y son
strings no vacíos. Si el módulo se refactoriza mal y se elimina
una constante, este test lo detecta inmediatamente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hit5"))

import ml_selectors  # noqa: E402

# ──────────────────────────────────────────────
# Constantes que deben existir (contrato público)
# ──────────────────────────────────────────────

EXPECTED_STRING_CONSTANTS = [
    "SEARCH_BOX_CSS",
    "RESULT_CARD_CSS",
    "CARD_TITLE_CSS",
    "CARD_PRICE_FRACTION_CSS",
    "CARD_LINK_CSS",
    "CARD_OFFICIAL_STORE_CSS",
    "CARD_FREE_SHIPPING_CSS",
    "CARD_INSTALLMENTS_CSS",
    "FILTER_NUEVO_XPATH",
    "FILTER_TIENDA_OFICIAL_XPATH",
    "SORT_BUTTON_CSS",
    "SORT_RELEVANCE_XPATH",
]

EXPECTED_LIST_CONSTANTS = [
    "COOKIE_BANNER_VARIANTS",
]


class TestConstantesExistentes:
    """Verifica que las constantes del módulo existan y sean strings no vacíos."""

    def test_constantes_string_existen(self) -> None:
        """Todas las constantes string deben existir en el módulo."""
        for nombre in EXPECTED_STRING_CONSTANTS:
            assert hasattr(ml_selectors, nombre), f"Falta la constante: {nombre}"

    def test_constantes_string_son_strings(self) -> None:
        """Cada constante debe ser de tipo str."""
        for nombre in EXPECTED_STRING_CONSTANTS:
            valor = getattr(ml_selectors, nombre)
            assert isinstance(valor, str), f"{nombre} no es str: {type(valor)}"

    def test_constantes_string_no_vacias(self) -> None:
        """Ninguna constante debe ser string vacío."""
        for nombre in EXPECTED_STRING_CONSTANTS:
            valor = getattr(ml_selectors, nombre)
            assert valor.strip(), f"{nombre} está vacía o solo tiene espacios"

    def test_cookie_banner_variants_existe(self) -> None:
        """COOKIE_BANNER_VARIANTS debe existir."""
        assert hasattr(ml_selectors, "COOKIE_BANNER_VARIANTS")

    def test_cookie_banner_variants_es_lista(self) -> None:
        """COOKIE_BANNER_VARIANTS debe ser una lista."""
        assert isinstance(ml_selectors.COOKIE_BANNER_VARIANTS, list)

    def test_cookie_banner_variants_no_vacia(self) -> None:
        """COOKIE_BANNER_VARIANTS debe tener al menos un elemento."""
        assert len(ml_selectors.COOKIE_BANNER_VARIANTS) > 0

    def test_cookie_banner_variants_son_tuplas(self) -> None:
        """Cada entrada de COOKIE_BANNER_VARIANTS debe ser una tupla de 2 strings."""
        for entry in ml_selectors.COOKIE_BANNER_VARIANTS:
            assert isinstance(entry, tuple), f"Entry no es tupla: {entry}"
            assert len(entry) == 2, f"Tupla no tiene 2 elementos: {entry}"  # noqa: PLR2004
            tipo, selector = entry
            assert isinstance(tipo, str), f"Tipo no es str: {tipo}"
            assert isinstance(selector, str), f"Selector no es str: {selector}"
            assert selector.strip(), f"Selector vacío en entry: {entry}"


class TestValoresEsperados:
    """Verifica que los valores de las constantes clave sean razonables."""

    def test_search_box_css_contiene_input(self) -> None:
        """El selector de la caja de búsqueda debe ser un input."""
        assert "input" in ml_selectors.SEARCH_BOX_CSS

    def test_result_card_css_no_vacio(self) -> None:
        """El selector de cards de resultado debe ser no vacío."""
        assert len(ml_selectors.RESULT_CARD_CSS) > 0

    def test_filter_nuevo_xpath_es_xpath(self) -> None:
        """El selector de filtro Nuevo debe empezar con '//' (XPath)."""
        assert ml_selectors.FILTER_NUEVO_XPATH.startswith("//")

    def test_cookie_banner_tipos_validos(self) -> None:
        """Los tipos de locator deben ser 'css' o 'xpath'."""
        tipos_validos = {"css", "xpath"}
        for tipo, _ in ml_selectors.COOKIE_BANNER_VARIANTS:
            assert tipo in tipos_validos, f"Tipo de locator inválido: {tipo}"
