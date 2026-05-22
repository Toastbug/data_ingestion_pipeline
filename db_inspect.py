# db_inspect.py
import psycopg2.extras
from db import get_dict_conn


def inspect():
    conn = get_dict_conn()
    cur = conn.cursor()

    # ── Queue ──────────────────────────────────────────────
    print("\n========== QUEUE (events_queue) ==========")
    cur.execute("""
        SELECT msg_id, enqueued_at, message
        FROM pgmq.q_events_queue
        ORDER BY enqueued_at
    """)
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  msg_id={r['msg_id']} | "
                  f"enqueued={r['enqueued_at']} | "
                  f"event={r['message'].get('event_type')} | "
                  f"user={r['message'].get('user_id')} | "
                  f"item={r['message'].get('item_id')}")
    else:
        print("  (empty)")

    # ── Items ──────────────────────────────────────────────
    print("\n========== ITEMS ==========")
    cur.execute("""
        SELECT id, project_id, external_id, title, created_at
        FROM items
        ORDER BY created_at
    """)
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  external_id={r['external_id']:12} | "
                  f"title={r['title']:20} | "
                  f"id={r['id']}")
    else:
        print("  (empty)")

    # ── Events ─────────────────────────────────────────────
    print("\n========== EVENTS ==========")
    cur.execute("""
        SELECT
            e.id,
            e.user_id,
            e.event_type,
            e.weight,
            e.device,
            e.received_at,
            i.external_id AS item
        FROM events e
        JOIN items i ON i.id = e.item_id
        ORDER BY e.received_at
    """)
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  user={r['user_id']} | "
                  f"{r['event_type']:12} | "
                  f"weight={r['weight']} | "
                  f"device={r['device']:8} | "
                  f"item={r['item']}")
    else:
        print("  (empty)")

    # ── Pending Events ─────────────────────────────────────
    print("\n========== PENDING EVENTS ==========")
    cur.execute("""
        SELECT
            user_id,
            event_type,
            item_id,
            retry_count,
            received_at,
            expires_at
        FROM pending_events
        ORDER BY received_at
    """)
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  user={r['user_id']} | "
                  f"{r['event_type']:12} | "
                  f"item={r['item_id']:12} | "
                  f"retries={r['retry_count']} | "
                  f"expires={r['expires_at']}")
    else:
        print("  (empty)")

    print()
    cur.close()
    conn.close()


if __name__ == "__main__":
    inspect()