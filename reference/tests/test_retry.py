"""Tests unitarios del decorador @with_backoff — hit5/retry.py.

Casos cubiertos:
- Éxito al primer intento (sin reintentos).
- Éxito en el intento 2 después de 1 fallo.
- Fallo total tras max_attempts.
- Excepción no-retryable se propaga sin reintento.
- El sleep se mockea para que los tests no sean lentos.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

sys.path.insert(0, str(Path(__file__).parent.parent / "hit5"))

from retry import DEFAULT_RETRYABLE, with_backoff  # noqa: E402

# ──────────────────────────────────────────────
# Tests de comportamiento básico
# ──────────────────────────────────────────────


class TestWithBackoffExito:
    """Tests del camino feliz del decorador."""

    def test_exito_primer_intento(self) -> None:
        """La función se llama una sola vez cuando no lanza excepción."""
        mock_fn = MagicMock(return_value="ok")

        @with_backoff(max_attempts=3, base_delay=0.01)
        def mi_funcion():
            return mock_fn()

        resultado = mi_funcion()

        assert resultado == "ok"
        assert mock_fn.call_count == 1

    def test_exito_segundo_intento(self) -> None:
        """Si falla una vez y la segunda tiene éxito, devuelve el resultado."""
        intentos = {"n": 0}

        @with_backoff(max_attempts=3, base_delay=0.001)
        def mi_funcion():
            intentos["n"] += 1
            if intentos["n"] < 2:
                raise TimeoutException("transitorio")
            return "exito"

        with patch("retry.time.sleep"):
            resultado = mi_funcion()

        assert resultado == "exito"
        assert intentos["n"] == 2

    def test_preserva_valor_de_retorno(self) -> None:
        """El decorador no modifica el valor de retorno de la función."""

        @with_backoff(max_attempts=2, base_delay=0.001)
        def devuelve_dict():
            return {"clave": 42}

        assert devuelve_dict() == {"clave": 42}

    def test_preserva_nombre_funcion(self) -> None:
        """functools.wraps debe preservar __name__ y __doc__."""

        @with_backoff(max_attempts=2, base_delay=0.001)
        def mi_funcion_especial():
            """Docstring de prueba."""
            return True

        assert mi_funcion_especial.__name__ == "mi_funcion_especial"
        assert "Docstring" in mi_funcion_especial.__doc__


# ──────────────────────────────────────────────
# Tests de fallo total
# ──────────────────────────────────────────────


class TestWithBackoffFalloTotal:
    """Tests del comportamiento cuando se agotan todos los intentos."""

    def test_fallo_total_relanza_ultima_excepcion(self) -> None:
        """Tras max_attempts fallidos, relanza la excepción original."""
        mock_fn = MagicMock(side_effect=TimeoutException("timeout persistente"))

        @with_backoff(max_attempts=3, base_delay=0.001)
        def mi_funcion():
            return mock_fn()

        with (
            patch("retry.time.sleep"),
            pytest.raises(TimeoutException, match="timeout persistente"),
        ):
            mi_funcion()

    def test_fallo_total_intenta_max_veces(self) -> None:
        """La función se llama exactamente max_attempts veces antes de rendirse."""
        mock_fn = MagicMock(side_effect=WebDriverException("error"))

        @with_backoff(max_attempts=4, base_delay=0.001)
        def mi_funcion():
            return mock_fn()

        with patch("retry.time.sleep"), pytest.raises(WebDriverException):
            mi_funcion()

        assert mock_fn.call_count == 4

    def test_backoff_exponencial_delays(self) -> None:
        """Verifica que los delays sean base * 2^(intento-1)."""
        mock_fn = MagicMock(side_effect=TimeoutException("error"))

        @with_backoff(max_attempts=3, base_delay=2.0)
        def mi_funcion():
            return mock_fn()

        with patch("retry.time.sleep") as mock_sleep, pytest.raises(TimeoutException):
            mi_funcion()

        # Intento 1 falla → sleep(2.0 * 2^0 = 2.0)
        # Intento 2 falla → sleep(2.0 * 2^1 = 4.0)
        # Intento 3 falla → lanza (no hay más sleep)
        assert mock_sleep.call_count == 2
        calls = mock_sleep.call_args_list
        assert calls[0] == call(2.0)
        assert calls[1] == call(4.0)

    def test_stale_element_es_retryable(self) -> None:
        """StaleElementReferenceException debe activar el reintento."""
        mock_fn = MagicMock(side_effect=StaleElementReferenceException("stale"))

        @with_backoff(max_attempts=2, base_delay=0.001)
        def mi_funcion():
            return mock_fn()

        with patch("retry.time.sleep"), pytest.raises(StaleElementReferenceException):
            mi_funcion()

        assert mock_fn.call_count == 2


# ──────────────────────────────────────────────
# Tests de excepción no-retryable
# ──────────────────────────────────────────────


class TestWithBackoffExcepcionNoRetryable:
    """Tests para excepciones que NO deben disparar reintento."""

    def test_valor_error_no_se_reintenta(self) -> None:
        """ValueError no está en DEFAULT_RETRYABLE → se propaga en el primer intento."""
        call_count = {"n": 0}

        @with_backoff(max_attempts=3, base_delay=0.001)
        def mi_funcion():
            call_count["n"] += 1
            raise ValueError("error de programación")

        with pytest.raises(ValueError, match="error de programación"):
            mi_funcion()

        # Solo se intentó una vez, no tres
        assert call_count["n"] == 1

    def test_runtime_error_no_se_reintenta(self) -> None:
        """RuntimeError tampoco está en DEFAULT_RETRYABLE."""
        call_count = {"n": 0}

        @with_backoff(max_attempts=3, base_delay=0.001, exceptions=(TimeoutException,))
        def mi_funcion():
            call_count["n"] += 1
            raise RuntimeError("error fatal")

        with pytest.raises(RuntimeError):
            mi_funcion()

        assert call_count["n"] == 1

    def test_excepciones_custom_retryables(self) -> None:
        """Se puede configurar qué excepciones son retryables."""

        class MiErrorTransitorio(Exception):
            pass

        mock_fn = MagicMock(side_effect=MiErrorTransitorio("transitorio"))

        @with_backoff(max_attempts=2, base_delay=0.001, exceptions=(MiErrorTransitorio,))
        def mi_funcion():
            return mock_fn()

        with patch("retry.time.sleep"), pytest.raises(MiErrorTransitorio):
            mi_funcion()

        assert mock_fn.call_count == 2


# ──────────────────────────────────────────────
# Tests de constantes y configuración
# ──────────────────────────────────────────────


class TestDefaultRetryable:
    """Tests que validan las excepciones retryable por defecto."""

    def test_default_retryable_incluye_timeout(self) -> None:
        assert TimeoutException in DEFAULT_RETRYABLE

    def test_default_retryable_incluye_stale(self) -> None:
        assert StaleElementReferenceException in DEFAULT_RETRYABLE

    def test_default_retryable_incluye_webdriver(self) -> None:
        assert WebDriverException in DEFAULT_RETRYABLE
