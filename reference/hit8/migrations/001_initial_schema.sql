-- 001_initial_schema.sql — Schema inicial para histórico del scraper
-- Aplicar con: psql $DATABASE_URL -f 001_initial_schema.sql

CREATE TABLE IF NOT EXISTS scrape_results (
    id              BIGSERIAL PRIMARY KEY,
    producto        TEXT NOT NULL,
    titulo          TEXT NOT NULL,
    precio          NUMERIC(12,2),
    link            TEXT,
    tienda_oficial  TEXT,
    envio_gratis    BOOLEAN,
    cuotas_sin_interes TEXT,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scrape_results_producto_fecha
    ON scrape_results (producto, scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_scrape_results_scraped_at
    ON scrape_results (scraped_at DESC);
