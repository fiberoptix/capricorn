-- Migration: Add live_pricing_enabled_at timestamp for GCP auto-disable feature
-- This tracks when live pricing was enabled so GCP can auto-disable after 20 minutes

ALTER TABLE user_profile 
ADD COLUMN IF NOT EXISTS live_pricing_enabled_at TIMESTAMP DEFAULT NULL;

-- Comment explaining the column
COMMENT ON COLUMN user_profile.live_pricing_enabled_at IS 'Timestamp when live pricing was enabled. Used by GCP deployment to auto-disable after 20 minutes.';

