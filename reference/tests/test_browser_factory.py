"""Tests de la cadena de resolución del browser — hit5/browser_factory.py.

Verifica la lógica de selección sin construir un driver real:
- Argumento explícito tiene prioridad sobre env var y default.
- Env var tiene prioridad sobre el default.
- Default es "chrome".
- Browser no soportado lanza ValueError.
- Flag HEADLESS se lee correctamente de env var.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "hit5"))

import browser_factory  # noqa: E402
from browser_factory import SUPPORTED_BROWSERS, _is_headless, create_driver  # noqa: E402

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _fake_chrome() -> MagicMock:
    """Simula una instancia de webdriver.Chrome."""
    d = MagicMock()
    d.capabilities = {"browserName": "chrome"}
    return d


def _fake_firefox() -> MagicMock:
    """Simula una instancia de webdriver.Firefox."""
    d = MagicMock()
    d.capabilities = {"browserName": "firefox"}
    return d


# ──────────────────────────────────────────────
# Tests de cadena de resolución del browser
# ──────────────────────────────────────────────


class TestCreateDriverResolucion:
    """Tests de la lógica de resolución: argumento > env var > default."""

    def test_argumento_explicito_chrome(self) -> None:
        """Argumento 'chrome' crea un Chrome sin importar la env var."""
        with (
            patch.object(
                browser_factory, "_build_chrome", return_value=_fake_chrome()
            ) as mock_chrome,
            patch.dict("os.environ", {"BROWSER": "firefox"}),
        ):
            create_driver(browser="chrome")
            mock_chrome.assert_called_once()

    def test_argumento_explicito_firefox(self) -> None:
        """Argumento 'firefox' crea un Firefox sin importar la env var."""
        with (
            patch.object(
                browser_factory, "_build_firefox", return_value=_fake_firefox()
            ) as mock_firefox,
            patch.dict("os.environ", {"BROWSER": "chrome"}),
        ):
            create_driver(browser="firefox")
            mock_firefox.assert_called_once()

    def test_env_var_chrome_sin_argumento(self) -> None:
        """Sin argumento explícito, BROWSER=chrome crea Chrome."""
        with (
            patch.object(
                browser_factory, "_build_chrome", return_value=_fake_chrome()
            ) as mock_chrome,
            patch.dict("os.environ", {"BROWSER": "chrome"}, clear=False),
        ):
            create_driver()
            mock_chrome.assert_called_once()

    def test_env_var_firefox_sin_argumento(self) -> None:
        """Sin argumento explícito, BROWSER=firefox crea Firefox."""
        with (
            patch.object(
                browser_factory, "_build_firefox", return_value=_fake_firefox()
            ) as mock_firefox,
            patch.dict("os.environ", {"BROWSER": "firefox"}, clear=False),
        ):
            create_driver()
            mock_firefox.assert_called_once()

    def test_default_chrome_sin_arg_ni_env(self) -> None:
        """Sin argumento ni env var, el default es Chrome."""
        with (
            patch.object(
                browser_factory, "_build_chrome", return_value=_fake_chrome()
            ) as mock_chrome,
            patch.dict("os.environ", {}, clear=True),
        ):
            # Asegurar que BROWSER no esté en el env
            import os

            os.environ.pop("BROWSER", None)
            create_driver()
            mock_chrome.assert_called_once()

    def test_argumento_mayusculas_normalizado(self) -> None:
        """El argumento se normaliza a minúsculas: 'Chrome' → 'chrome'."""
        with patch.object(
            browser_factory, "_build_chrome", return_value=_fake_chrome()
        ) as mock_chrome:
            create_driver(browser="Chrome")
            mock_chrome.assert_called_once()

    def test_argumento_con_espacios_normalizado(self) -> None:
        """El argumento se hace strip: ' firefox ' → 'firefox'."""
        with patch.object(
            browser_factory, "_build_firefox", return_value=_fake_firefox()
        ) as mock_firefox:
            create_driver(browser=" firefox ")
            mock_firefox.assert_called_once()


# ──────────────────────────────────────────────
# Tests de error por browser no soportado
# ──────────────────────────────────────────────


class TestCreateDriverErrores:
    """Tests de validación de browser no soportado."""

    def test_browser_invalido_lanza_value_error(self) -> None:
        """Browser desconocido debe lanzar ValueError con mensaje descriptivo."""
        with pytest.raises(ValueError, match="safari"):
            create_driver(browser="safari")

    def test_browser_vacio_lanza_value_error(self) -> None:
        """String vacío como browser lanza ValueError."""
        with pytest.raises(ValueError):
            create_driver(browser="")

    def test_mensaje_error_incluye_opciones_validas(self) -> None:
        """El mensaje de error menciona los browsers soportados."""
        with pytest.raises(ValueError) as exc_info:
            create_driver(browser="edge")
        assert "chrome" in str(exc_info.value).lower() or "firefox" in str(exc_info.value).lower()


# ──────────────────────────────────────────────
# Tests de detección de headless
# ──────────────────────────────────────────────


class TestIsHeadless:
    """Tests de la función auxiliar _is_headless."""

    def test_headless_false_por_defecto(self) -> None:
        """Sin env var, headless es False."""
        with patch.dict("os.environ", {}, clear=True):
            import os

            os.environ.pop("HEADLESS", None)
            assert _is_headless() is False

    @pytest.mark.parametrize("valor", ["1", "true", "True", "TRUE", "yes", "Yes", "YES"])
    def test_headless_true_variantes(self, valor: str) -> None:
        """HEADLESS acepta múltiples representaciones de verdadero."""
        with patch.dict("os.environ", {"HEADLESS": valor}):
            assert _is_headless() is True

    @pytest.mark.parametrize("valor", ["0", "false", "no", "False", ""])
    def test_headless_false_variantes(self, valor: str) -> None:
        """Valores no-truthy dejan headless en False."""
        with patch.dict("os.environ", {"HEADLESS": valor}):
            assert _is_headless() is False


# ──────────────────────────────────────────────
# Tests de constantes
# ──────────────────────────────────────────────


class TestSupportedBrowsers:
    """Tests de la constante SUPPORTED_BROWSERS."""

    def test_chrome_en_supported(self) -> None:
        assert "chrome" in SUPPORTED_BROWSERS

    def test_firefox_en_supported(self) -> None:
        assert "firefox" in SUPPORTED_BROWSERS

    def test_supported_browsers_es_tupla(self) -> None:
        assert isinstance(SUPPORTED_BROWSERS, tuple)
