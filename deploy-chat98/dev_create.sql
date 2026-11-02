-- chat98: tables for in-app alerts and Portfolio X-ray.
-- Run once by hand in the Replit database console (dev first). CREATE TABLE IF NOT EXISTS only:
-- no DROP, no ALTER, safe to run twice. The app never runs DDL; it checks these with to_regclass
-- and hides Alerts / Portfolio X-ray until they exist.

CREATE TABLE IF NOT EXISTS dispatch_alerts (
  id            BIGSERIAL PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES dispatch_users(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL CHECK (kind IN ('price', 'level', 'macro')),
  subject       TEXT NOT NULL CHECK (char_length(subject) <= 80),
  op            TEXT NOT NULL CHECK (op IN ('above', 'below', 'release')),
  threshold     DOUBLE PRECISION,
  note          TEXT CHECK (note IS NULL OR char_length(note) <= 140),
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  armed         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_fired_at TIMESTAMPTZ,
  last_value    DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS dispatch_alert_events (
  id        BIGSERIAL PRIMARY KEY,
  alert_id  BIGINT NOT NULL REFERENCES dispatch_alerts(id) ON DELETE CASCADE,
  user_id   TEXT NOT NULL REFERENCES dispatch_users(id) ON DELETE CASCADE,
  fired_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  value     DOUBLE PRECISION,
  message   TEXT NOT NULL CHECK (char_length(message) <= 400),
  seen      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dispatch_portfolio (
  user_id    TEXT PRIMARY KEY REFERENCES dispatch_users(id) ON DELETE CASCADE,
  holdings   JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
