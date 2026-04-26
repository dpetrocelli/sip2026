"""Tests unitarios de los extractores de campos — hit5/extractors.py.

Cubre los 6 extractores usando mocks de WebElement, sin browser real.
Casos: campo presente, campo ausente, precio con caracteres raros,
link absoluto vs relativo, envío gratis presente/ausente.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

from selenium.common.exceptions import NoSuchElementException

sys.path.insert(0, str(Path(__file__).parent.parent / "hit5"))

from extractors import (  # noqa: E402
    extract_cuotas_sin_interes,
    extract_envio_gratis,
    extract_link,
    extract_precio,
    extract_result,
    extract_tienda_oficial,
    extract_titulo,
)

# ──────────────────────────────────────────────
# Helpers locales
# ──────────────────────────────────────────────


def _elem(text: str = "", href: str | None = None) -> MagicMock:
    """Crea un WebElement fake con texto y/o href."""
    e = MagicMock()
    e.text = text
    e.get_attribute.side_effect = lambda attr: href if attr == "href" else None
    return e


def _card_with(selector_results: dict) -> MagicMock:
    """Crea una card fake donde find_element devuelve lo que dicte el mapa.

    Si el valor del mapa es None, lanza NoSuchElementException.
    """

    def _find(by, sel):  # noqa: ANN001
        result = selector_results.get(sel)
        if result is None:
            raise NoSuchElementException(sel)
        return result

    card = MagicMock()
    card.find_element.side_effect = _find
    return card


# ──────────────────────────────────────────────
# extract_titulo
# ──────────────────────────────────────────────


class TestExtractTitulo:
    """Tests del extractor de título."""

    def test_titulo_presente(self) -> None:
        """Cuando el elemento de título existe, devuelve el texto sin espacios extra."""
        from extractors import SEL_TITLE

        card = _card_with({SEL_TITLE: _elem("  Bicicleta Rodado 29  ")})
        assert extract_titulo(card) == "Bicicleta Rodado 29"

    def test_titulo_ausente(self) -> None:
        """Cuando no hay título en el DOM, devuelve None sin explotar."""
        from extractors import SEL_TITLE

        card = _card_with({SEL_TITLE: None})
        assert extract_titulo(card) is None

    def test_titulo_texto_vacio(self) -> None:
        """Texto vacío (strip) se normaliza a None."""
        from extractors import SEL_TITLE

        card = _card_with({SEL_TITLE: _elem("   ")})
        result = extract_titulo(card)
        # strip() → "" → falsy → None
        assert result is None


# ──────────────────────────────────────────────
# extract_precio
# ──────────────────────────────────────────────


class TestExtractPrecio:
    """Tests del extractor de precio."""

    def test_precio_entero_simple(self) -> None:
        """Precio sin separadores de miles devuelve float correcto."""
        from extractors import SEL_PRICE_FRACTION

        card = _card_with({SEL_PRICE_FRACTION: _elem("250000")})
        assert extract_precio(card) == 250000.0

    def test_precio_con_puntos_separadores(self) -> None:
        """ML usa punto como separador de miles: '250.000' → 250000.0."""
        from extractors import SEL_PRICE_FRACTION

        card = _card_with({SEL_PRICE_FRACTION: _elem("250.000")})
        assert extract_precio(card) == 250000.0

    def test_precio_con_simbolo_peso(self) -> None:
        """El símbolo $ y espacios se eliminan correctamente."""
        from extractors import SEL_PRICE_FRACTION

        card = _card_with({SEL_PRICE_FRACTION: _elem("$ 1.500.000")})
        assert extract_precio(card) == 1500000.0

    def test_precio_ausente(self) -> None:
        """Sin elemento de precio, devuelve None."""
        from extractors import SEL_PRICE_FRACTION

        card = _card_with({SEL_PRICE_FRACTION: None})
        assert extract_precio(card) is None

    def test_precio_texto_no_numerico(self) -> None:
        """Texto que no contiene dígitos devuelve None."""
        from extractors import SEL_PRICE_FRACTION

        card = _card_with({SEL_PRICE_FRACTION: _elem("N/A")})
        assert extract_precio(card) is None


# ──────────────────────────────────────────────
# extract_link
# ──────────────────────────────────────────────


class TestExtractLink:
    """Tests del extractor de link al detalle del producto."""

    def test_link_absoluto(self) -> None:
        """Href absoluto (https://...) se devuelve tal cual."""
        from extractors import SEL_LINK

        url = "https://articulo.mercadolibre.com.ar/MLA-123-bicicleta_JM"
        card = _card_with({SEL_LINK: _elem(href=url)})
        assert extract_link(card) == url

    def test_link_relativo_descartado(self) -> None:
        """Href relativo (no empieza con 'http') se descarta → None."""
        from extractors import SEL_LINK

        card = _card_with({SEL_LINK: _elem(href="/MLA-123")})
        assert extract_link(card) is None

    def test_link_ausente(self) -> None:
        """Sin elemento de link, devuelve None."""
        from extractors import SEL_LINK

        card = _card_with({SEL_LINK: None})
        assert extract_link(card) is None

    def test_link_href_none(self) -> None:
        """Elemento existe pero get_attribute('href') devuelve None → None."""
        from extractors import SEL_LINK

        card = _card_with({SEL_LINK: _elem(href=None)})
        assert extract_link(card) is None


# ──────────────────────────────────────────────
# extract_tienda_oficial
# ──────────────────────────────────────────────


class TestExtractTiendaOficial:
    """Tests del extractor de tienda oficial."""

    def test_tienda_oficial_presente(self) -> None:
        """Cuando el elemento existe, devuelve el texto del nombre."""
        from extractors import SEL_OFFICIAL_STORE

        card = _card_with({SEL_OFFICIAL_STORE: _elem("Trek Store")})
        assert extract_tienda_oficial(card) == "Trek Store"

    def test_tienda_oficial_ausente(self) -> None:
        """Sin el elemento, devuelve None (no lanza excepción)."""
        from extractors import SEL_OFFICIAL_STORE

        card = _card_with({SEL_OFFICIAL_STORE: None})
        assert extract_tienda_oficial(card) is None

    def test_tienda_oficial_texto_vacio(self) -> None:
        """Texto vacío tras strip() devuelve None."""
        from extractors import SEL_OFFICIAL_STORE

        card = _card_with({SEL_OFFICIAL_STORE: _elem("  ")})
        assert extract_tienda_oficial(card) is None


# ──────────────────────────────────────────────
# extract_envio_gratis
# ──────────────────────────────────────────────


class TestExtractEnvioGratis:
    """Tests del detector de envío gratis."""

    def test_envio_gratis_espanol(self) -> None:
        """Texto con 'gratis' → True."""
        from extractors import SEL_FREE_SHIPPING

        card = _card_with({SEL_FREE_SHIPPING: _elem("Llega gratis el miércoles")})
        assert extract_envio_gratis(card) is True

    def test_envio_gratis_ingles(self) -> None:
        """Texto con 'free' (en inglés) → True."""
        from extractors import SEL_FREE_SHIPPING

        card = _card_with({SEL_FREE_SHIPPING: _elem("Free shipping")})
        assert extract_envio_gratis(card) is True

    def test_envio_no_gratis(self) -> None:
        """Texto sin 'gratis' ni 'free' → False."""
        from extractors import SEL_FREE_SHIPPING

        card = _card_with({SEL_FREE_SHIPPING: _elem("Llega en 5 días")})
        assert extract_envio_gratis(card) is False

    def test_envio_elemento_ausente(self) -> None:
        """Sin elemento de envío, devuelve False (default seguro)."""
        from extractors import SEL_FREE_SHIPPING

        card = _card_with({SEL_FREE_SHIPPING: None})
        assert extract_envio_gratis(card) is False

    def test_envio_gratis_mayusculas(self) -> None:
        """La comparación es case-insensitive."""
        from extractors import SEL_FREE_SHIPPING

        card = _card_with({SEL_FREE_SHIPPING: _elem("ENVÍO GRATIS")})
        assert extract_envio_gratis(card) is True


# ──────────────────────────────────────────────
# extract_cuotas_sin_interes
# ──────────────────────────────────────────────


class TestExtractCuotasSinInteres:
    """Tests del extractor de cuotas sin interés."""

    def test_cuotas_presente(self) -> None:
        """Cuando el elemento existe, devuelve el texto."""
        from extractors import SEL_INSTALLMENTS

        card = _card_with({SEL_INSTALLMENTS: _elem("12x sin interés")})
        assert extract_cuotas_sin_interes(card) == "12x sin interés"

    def test_cuotas_ausente(self) -> None:
        """Sin elemento, devuelve None."""
        from extractors import SEL_INSTALLMENTS

        card = _card_with({SEL_INSTALLMENTS: None})
        assert extract_cuotas_sin_interes(card) is None

    def test_cuotas_texto_vacio(self) -> None:
        """Texto vacío devuelve None."""
        from extractors import SEL_INSTALLMENTS

        card = _card_with({SEL_INSTALLMENTS: _elem("")})
        assert extract_cuotas_sin_interes(card) is None


# ──────────────────────────────────────────────
# extract_result (integración de extractores)
# ──────────────────────────────────────────────


class TestExtractResult:
    """Tests del extractor compuesto que llama a todos los sub-extractores."""

    def test_result_completo(self) -> None:
        """Con una card completa, devuelve dict con los 6 campos correctos."""
        from extractors import (
            SEL_FREE_SHIPPING,
            SEL_INSTALLMENTS,
            SEL_LINK,
            SEL_OFFICIAL_STORE,
            SEL_PRICE_FRACTION,
            SEL_TITLE,
        )

        url = "https://articulo.mercadolibre.com.ar/MLA-123"
        card = _card_with(
            {
                SEL_TITLE: _elem("Bicicleta"),
                SEL_PRICE_FRACTION: _elem("250.000"),
                SEL_LINK: _elem(href=url),
                SEL_OFFICIAL_STORE: _elem("Trek Store"),
                SEL_FREE_SHIPPING: _elem("Llega gratis"),
                SEL_INSTALLMENTS: _elem("6x sin interés"),
            }
        )
        result = extract_result(card)

        assert result["titulo"] == "Bicicleta"
        assert result["precio"] == 250000.0
        assert result["link"] == url
        assert result["tienda_oficial"] == "Trek Store"
        assert result["envio_gratis"] is True
        assert result["cuotas_sin_interes"] == "6x sin interés"

    def test_result_vacio_no_explota(self) -> None:
        """Una card sin ningún campo devuelve dict con valores None/False."""
        from extractors import (
            SEL_FREE_SHIPPING,
            SEL_INSTALLMENTS,
            SEL_LINK,
            SEL_OFFICIAL_STORE,
            SEL_PRICE_FRACTION,
            SEL_TITLE,
        )

        card = _card_with(
            {
                SEL_TITLE: None,
                SEL_PRICE_FRACTION: None,
                SEL_LINK: None,
                SEL_OFFICIAL_STORE: None,
                SEL_FREE_SHIPPING: None,
                SEL_INSTALLMENTS: None,
            }
        )
        result = extract_result(card)

        assert result["titulo"] is None
        assert result["precio"] is None
        assert result["link"] is None
        assert result["tienda_oficial"] is None
        assert result["envio_gratis"] is False
        assert result["cuotas_sin_interes"] is None

    def test_result_tiene_claves_correctas(self) -> None:
        """El dict devuelto siempre tiene exactamente las 6 claves del schema."""
        from extractors import (
            SEL_FREE_SHIPPING,
            SEL_INSTALLMENTS,
            SEL_LINK,
            SEL_OFFICIAL_STORE,
            SEL_PRICE_FRACTION,
            SEL_TITLE,
        )

        card = _card_with(
            {
                SEL_TITLE: None,
                SEL_PRICE_FRACTION: None,
                SEL_LINK: None,
                SEL_OFFICIAL_STORE: None,
                SEL_FREE_SHIPPING: None,
                SEL_INSTALLMENTS: None,
            }
        )
        result = extract_result(card)
        expected_keys = {
            "titulo",
            "precio",
            "link",
            "tienda_oficial",
            "envio_gratis",
            "cuotas_sin_interes",
        }
        assert set(result.keys()) == expected_keys
