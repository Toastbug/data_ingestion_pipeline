# producer.py
import json
from datetime import datetime, timezone
from db import get_conn

QUEUE = 'events_queue'

def send_event(event: dict):
    """Send a single event into the PGMQ queue."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT pgmq.send(%s, %s::jsonb)",
        (QUEUE, json.dumps(event))
    )

    msg_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    print(f"  Queued → msg_id: {msg_id} | {event['event_type']} | user: {event['user_id']} | item: {event['item_id']}")
    return msg_id


if __name__ == "__main__":
    print("\n--- Sending test events to queue ---\n")

    # Event 1 — item EXISTS (will land in events table)
    send_event({
        "project_id": "shop-x",
        "user_id": "usr_001",
        "item_id": "prod_abc",
        "item_type": "product",
        "event_type": "purchase",
        "weight": 5.0,
        "session_id": "sess_111",
        "device": "mobile",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {"referrer": "recommendation"}
    })

    # Event 2 — item DOES NOT EXIST yet (will land in pending_events)
    send_event({
        "project_id": "shop-x",
        "user_id": "usr_002",
        "item_id": "prod_xyz",
        "item_type": "product",
        "event_type": "click",
        "weight": 2.0,
        "session_id": "sess_222",
        "device": "desktop",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {}
    })

    # Event 3 — item EXISTS (will land in events table)
    send_event({
        "project_id": "shop-x",
        "user_id": "usr_003",
        "item_id": "prod_abc",
        "item_type": "product",
        "event_type": "view",
        "weight": 1.0,
        "session_id": "sess_333",
        "device": "tablet",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {}
    })

    print("\n--- Done. Run worker.py to process them ---\n")