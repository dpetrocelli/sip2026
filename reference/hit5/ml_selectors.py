"""Selectores centralizados para MercadoLibre — Hit #5.

Todos los selectores CSS/XPath del scraper viven acá. Un cambio del
DOM de ML se arregla actualizando este archivo en un único lugar
(criterio de calidad de la rúbrica del TP).

Convención: constantes con nombres semánticos, agrupadas por concepto.
"""

# ──────────────────────────────────────────────
# Búsqueda
# ──────────────────────────────────────────────

SEARCH_BOX_CSS = "input.nav-search-input"

# ──────────────────────────────────────────────
# Listado de resultados
# ──────────────────────────────────────────────

RESULT_CARD_CSS = "li.ui-search-layout__item, div.ui-search-result__wrapper"

# ──────────────────────────────────────────────
# Campos por card de resultado
# ──────────────────────────────────────────────

CARD_TITLE_CSS = "h2.ui-search-item__title, h2.poly-component__title, a.poly-component__title"
CARD_PRICE_FRACTION_CSS = "span.andes-money-amount__fraction"
CARD_LINK_CSS = "a.ui-search-link, a.poly-component__title-wrapper, h2 a"
CARD_OFFICIAL_STORE_CSS = (
    "span.poly-component__official, "
    "span.ui-search-official-store-label, "
    "span[class*='official-store']"
)
CARD_FREE_SHIPPING_CSS = "p.ui-search-item__shipping, p[class*='shipping'], span[class*='shipping']"
CARD_INSTALLMENTS_CSS = "span.ui-search-installments, span[class*='installments']"

# ──────────────────────────────────────────────
# Banner de cookies
# ──────────────────────────────────────────────

COOKIE_BANNER_VARIANTS = [
    ("css", "button#newCookieBanner"),
    ("css", "button[data-testid='action:understood-button']"),
    ("css", "button.cookie-consent-banner-opt-in"),
    ("xpath", "//button[contains(text(),'Entendido')]"),
    ("xpath", "//button[contains(text(),'Acepto')]"),
    ("xpath", "//button[contains(text(),'Aceptar')]"),
]

# ──────────────────────────────────────────────
# Filtros del panel lateral
# ──────────────────────────────────────────────

FILTER_NUEVO_XPATH = (
    "//span[normalize-space(text())='Nuevo']/ancestor::a | "
    "//a[normalize-space(text())='Nuevo'] | "
    "//li[contains(@class,'ui-search-filter')]//span[text()='Nuevo']/parent::a"
)
FILTER_TIENDA_OFICIAL_XPATH = (
    "//span[normalize-space(text())='Sí']/ancestor::a[1] | "
    "//a[normalize-space(text())='Sí'] | "
    "//li[contains(@class,'ui-search-filter')]//span[text()='Sí']/parent::a"
)

# ──────────────────────────────────────────────
# Ordenamiento
# ──────────────────────────────────────────────

SORT_BUTTON_CSS = (
    "button.andes-dropdown__trigger, "
    "[class*='ui-search-sort'] button, "
    "[class*='sort-filter'] button"
)
SORT_RELEVANCE_XPATH = (
    "//li[contains(@class,'andes-list__item')]//span[contains(text(),'relevante')] | "
    "//li[contains(@class,'andes-dropdown')]//span[contains(text(),'relevante')]"
)
