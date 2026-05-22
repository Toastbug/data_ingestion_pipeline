# worker.py
import json
import time
import psycopg2.extras
from db import get_conn

QUEUE = 'events_queue'
VISIBILITY_TIMEOUT = 30  # seconds a message is hidden after being read
BATCH_SIZE = 5           # how many messages to read per poll
POLL_INTERVAL = 2        # seconds to wait when queue is empty


def seed_item(cur):
    """
    Insert a known test item into items table.
    prod_abc exists → events will resolve.
    prod_xyz does not exist → events will go to pending_events.
    """
    cur.execute("""
        INSERT INTO items (project_id, external_id, item_type, title)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (project_id, external_id) DO NOTHING
    """, ('shop-x', 'prod_abc', 'product', 'Test Product ABC'))
    print("  Seeded item: prod_abc")
    print("  Item prod_xyz intentionally missing — to test pending path\n")


def process_event(cur, event: dict) -> str:
    """
    Check if item exists in items table.
    If yes  → insert into events.
    If no   → insert into pending_events.
    Returns 'inserted' or 'pending'.
    """

    # Check if item exists
    cur.execute(
        "SELECT id FROM items WHERE project_id = %s AND external_id = %s",
        (event['project_id'], event['item_id'])
    )
    item = cur.fetchone()

    if item:
        # Item found — insert into events
        item_uuid = item['id']
        cur.execute("""
            INSERT INTO events
              (project_id, user_id, item_id, item_type, event_type,
               weight, session_id, device, timestamp, context)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event['project_id'],
            event['user_id'],
            item_uuid,
            event['item_type'],
            event['event_type'],
            event['weight'],
            event['session_id'],
            event['device'],
            event['timestamp'],
            json.dumps(event.get('context', {}))
        ))
        return 'inserted'

    else:
        # Item not found — buffer into pending_events
        cur.execute("""
            INSERT INTO pending_events
              (project_id, user_id, item_id, item_type, event_type,
               weight, session_id, device, timestamp, context)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event['project_id'],
            event['user_id'],
            event['item_id'],
            event['item_type'],
            event['event_type'],
            event['weight'],
            event['session_id'],
            event['device'],
            event['timestamp'],
            json.dumps(event.get('context', {}))
        ))
        return 'pending'


def run():
    print("\n--- Worker started. Polling events_queue ---\n")

    conn = get_conn()
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cur = conn.cursor()

    # Seed the test item before processing
    seed_item(cur)
    conn.commit()

    processed = 0

    while True:
        # Read up to BATCH_SIZE messages from the queue
        cur.execute(
            "SELECT * FROM pgmq.read(%s, %s, %s)",
            (QUEUE, VISIBILITY_TIMEOUT, BATCH_SIZE)
        )
        messages = cur.fetchall()

        if not messages:
            if processed > 0:
                # Queue is empty and we processed something — stop
                print(f"\n--- Queue empty. Processed {processed} message(s). Done. ---\n")
                break
            # Queue was empty from the start — wait and retry
            print("  Waiting for messages...")
            time.sleep(POLL_INTERVAL)
            continue

        for msg in messages:
            msg_id = msg['msg_id']
            event  = msg['message']

            try:
                outcome = process_event(cur, event)

                # Delete message from queue — successfully processed
                cur.execute(
                    "SELECT pgmq.delete(%s, %s)",
                    (QUEUE, msg_id)
                )

                conn.commit()
                processed += 1

                icon = "✓" if outcome == 'inserted' else "⏳"
                print(f"  {icon}  msg_id={msg_id} | {outcome:8} | "
                      f"{event['event_type']:12} | "
                      f"user={event['user_id']} | "
                      f"item={event['item_id']}")

            except Exception as e:
                conn.rollback()
                print(f"  ✗  msg_id={msg_id} | FAILED: {e}")
                # Message stays in queue and reappears after VISIBILITY_TIMEOUT

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()