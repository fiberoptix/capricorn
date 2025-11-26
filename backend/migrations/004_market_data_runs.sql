-- Create table to track automatic market data refresh runs
-- Ensures at most one 'startup' and one 'close' run per day
-- This prevents excessive API calls to TwelveData

CREATE TABLE IF NOT EXISTS market_data_runs (
  id SERIAL PRIMARY KEY,
  run_type VARCHAR(20) NOT NULL CHECK (run_type IN ('startup','close')),
  run_date DATE NOT NULL,
  run_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (run_type, run_date)
);

CREATE INDEX IF NOT EXISTS idx_market_data_runs_date ON market_data_runs(run_date);
CREATE INDEX IF NOT EXISTS idx_market_data_runs_type ON market_data_runs(run_type);

