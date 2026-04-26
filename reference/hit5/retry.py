"""Decorador de retries con backoff exponencial — Hit #5.

Aplica reintentos con espera 2s/4s/8s ante excepciones transitorias
de Selenium (TimeoutException, StaleElementReferenceException,
WebDriverException). Loguea cada reintento con contexto.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import TypeVar

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_RETRYABLE = (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)


def with_backoff(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    exceptions: tuple[type[BaseException], ...] = DEFAULT_RETRYABLE,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decora una función con reintentos con backoff exponencial.

    Espera entre intentos: base_delay * 2**(intento-1). Con base_delay=2
    y max_attempts=3 → 2s, 4s, 8s.

    Args:
        max_attempts: Cantidad total de intentos (incluye el primero).
        base_delay: Delay base en segundos para el backoff.
        exceptions: Tupla de excepciones que disparan reintento.

    Returns:
        Decorador.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "%s falló tras %d intentos: %s",
                            func.__name__,
                            max_attempts,
                            exc,
                        )
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "%s intento %d/%d falló (%s), reintentando en %.1fs",
                        func.__name__,
                        attempt,
                        max_attempts,
                        type(exc).__name__,
                        delay,
                    )
                    time.sleep(delay)
            # Defensivo: nunca debería llegar acá
            if last_exc is not None:
                raise last_exc
            raise RuntimeError(f"{func.__name__} agotó intentos sin excepción capturada")

        return wrapper

    return decorator
