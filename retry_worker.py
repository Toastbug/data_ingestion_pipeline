# retry_worker.py
import json
import psycopg2.extras
from db import get_conn


def move_to_event_status(cur, row, status, reason):
    cur.execute("""
        INSERT INTO event_status (
            original_id, project_id, user_id, item_id, item_type,
            event_type, weight, session_id, device, timestamp,
            received_at, retry_count, status, reason
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['id'],
        row['project_id'],
        row['user_id'],
        row['item_id'],
        row['item_type'],
        row['event_type'],
        row['weight'],
        row['session_id'],
        row['device'],
        row['timestamp'],
        row['received_at'],
        row['retry_count'],
        status,
        reason
    ))


def resolve_pending():
    conn = get_conn()
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cur = conn.cursor()

    resolved = 0
    expired  = 0
    skipped  = 0
    failed   = 0

    # ── Step 1 — expired rows ─────────────────────────────
    cur.execute("""
        SELECT * FROM pending_events
        WHERE expires_at <= now()
        ORDER BY received_at
    """)
    expired_rows = cur.fetchall()

    if expired_rows:
        print(f"  Found {len(expired_rows)} expired event(s). Moving to event_status...\n")
        expired_ids = []

        for row in expired_rows:
            try:
                move_to_event_status(
                    cur, row,
                    status='expired',
                    reason='item_not_found_within_24h'
                )
                expired_ids.append(row['id'])
                expired += 1
                print(f"  ✗  Expired | user={row['user_id']} | "
                      f"item={row['item_id']} | "
                      f"retries={row['retry_count']}")
            except Exception as e:
                failed += 1
                print(f"  !  Failed to move expired row | {e}")

        # One bulk delete for all expired rows
        if expired_ids:
            cur.execute("""
                DELETE FROM pending_events
                WHERE id = ANY(%s::uuid[])
            """, (expired_ids,))
        conn.commit()

    # ── Step 2 — active rows ──────────────────────────────
    cur.execute("""
        SELECT * FROM pending_events
        WHERE expires_at > now()
        ORDER BY received_at
    """)
    active_rows = cur.fetchall()

    if not active_rows:
        print("\n  No active pending events found.")
    else:
        print(f"\n  Found {len(active_rows)} active pending event(s). Processing...\n")

        resolved_ids = []
        failed_ids   = []

        for row in active_rows:
            try:
                cur.execute("""
                    SELECT id FROM items
                    WHERE project_id = %s AND external_id = %s
                """, (row['project_id'], row['item_id']))
                item = cur.fetchone()

                if item:
                    cur.execute("""
                        INSERT INTO events (
                            project_id, user_id, item_id, item_type,
                            event_type, weight, session_id, device,
                            timestamp, context
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['project_id'],
                        row['user_id'],
                        item['id'],
                        row['item_type'],
                        row['event_type'],
                        row['weight'],
                        row['session_id'],
                        row['device'],
                        row['timestamp'],
                        json.dumps(row['context']) if row['context'] else '{}'
                    ))
                    move_to_event_status(
                        cur, row,
                        status='resolved',
                        reason='item_found_on_retry'
                    )
                    resolved_ids.append(row['id'])
                    resolved += 1
                    print(f"  ✓  Resolved | user={row['user_id']} | "
                          f"{row['event_type']:12} | "
                          f"item={row['item_id']} | "
                          f"retries={row['retry_count']}")

                else:
                    cur.execute("""
                        UPDATE pending_events
                        SET retry_count = retry_count + 1
                        WHERE id = %s
                    """, (row['id'],))
                    skipped += 1
                    print(f"  ⏳  Still pending | user={row['user_id']} | "
                          f"item={row['item_id']} | "
                          f"retries={row['retry_count'] + 1}")

            except Exception as e:
                failed += 1
                print(f"  !  Error | user={row['user_id']} | {e}")
                try:
                    move_to_event_status(
                        cur, row,
                        status='failed',
                        reason=str(e)
                    )
                    failed_ids.append(row['id'])
                except Exception as inner_e:
                    print(f"  !  Could not record failure | {inner_e}")

        # One bulk delete for resolved rows
        if resolved_ids:
            cur.execute("""
                DELETE FROM pending_events
                WHERE id = ANY(%s::uuid[])
            """, (resolved_ids,))

        # One bulk delete for failed rows
        if failed_ids:
            cur.execute("""
                DELETE FROM pending_events
                WHERE id = ANY(%s::uuid[])
            """, (failed_ids,))

        # One single commit for everything
        conn.commit()

    # ── Summary ───────────────────────────────────────────
    print(f"""
  ── Summary ──────────────────────────
  ✓  Resolved  : {resolved}
  ✗  Expired   : {expired}
  ⏳  Pending   : {skipped}
  !  Failed    : {failed}
  ─────────────────────────────────────
    """)

    cur.close()
    conn.close()


if __name__ == "__main__":
    print("\n--- Retry worker started ---\n")
    resolve_pending()
