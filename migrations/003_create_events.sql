CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    item_id UUID NOT NULL REFERENCES items(id),
    item_type TEXT NOT NULL CHECK (item_type IN ('product','content')),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'view','click','scroll_75','add_to_cart','wishlist',
        'video_finish','article_read','purchase','hide',
        'not_interested','return'
    )),
    weight NUMERIC(4,2) NOT NULL,
    session_id TEXT NOT NULL,
    device TEXT NOT NULL CHECK (device IN ('mobile','desktop','tablet')),
    timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    context JSONB DEFAULT '{}'::JSONB
);