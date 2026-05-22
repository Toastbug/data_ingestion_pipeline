CREATE TABLE pending_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    weight NUMERIC(4,2) NOT NULL,
    session_id TEXT NOT NULL,
    device TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    context JSONB DEFAULT '{}'::JSONB,
    retry_count INT DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '24 hours'
);