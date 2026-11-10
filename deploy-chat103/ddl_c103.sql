-- chat103 new tables only. Each statement creates one of the five cpi_ tables if it is missing.
CREATE TABLE IF NOT EXISTS cpi_releases (
    period TEXT PRIMARY KEY,
    release_at TIMESTAMPTZ,
    release_source TEXT NOT NULL,
    reference_label TEXT,
    headline_mom DOUBLE PRECISION,
    headline_yoy DOUBLE PRECISION,
    core_mom DOUBLE PRECISION,
    core_yoy DOUBLE PRECISION,
    bls_fetched_at TIMESTAMPTZ,
    payload JSONB,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

CREATE TABLE IF NOT EXISTS cpi_series_values (
    series_id TEXT NOT NULL,
    period TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (series_id, period)
  );

CREATE TABLE IF NOT EXISTS cpi_gold_reactions (
    release_at TIMESTAMPTZ PRIMARY KEY,
    reference_period TEXT,
    anchor_at TIMESTAMPTZ,
    anchor_price DOUBLE PRECISION,
    plus_1h_at TIMESTAMPTZ,
    plus_1h_price DOUBLE PRECISION,
    plus_1h_pct DOUBLE PRECISION,
    plus_1d_session TEXT,
    plus_1d_price DOUBLE PRECISION,
    plus_1d_pct DOUBLE PRECISION,
    plus_5d_session TEXT,
    plus_5d_price DOUBLE PRECISION,
    plus_5d_pct DOUBLE PRECISION,
    hourly_available BOOLEAN NOT NULL DEFAULT FALSE,
    recorded BOOLEAN NOT NULL DEFAULT FALSE,
    hour_label TEXT,
    source_label TEXT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

CREATE TABLE IF NOT EXISTS cpi_gold_snapshots (
    id BIGSERIAL PRIMARY KEY,
    release_at TIMESTAMPTZ NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    window_kind TEXT NOT NULL,
    source_label TEXT NOT NULL,
    UNIQUE (release_at, window_kind, observed_at)
  );

CREATE TABLE IF NOT EXISTS cpi_notice_dismissals (
    user_id TEXT NOT NULL,
    release_key TEXT NOT NULL,
    dismissed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, release_key)
  );
