# catalog_sync.py
import json
import psycopg2
import psycopg2.extras
from db import get_conn
from decimal import Decimal

CONFIG_PATH = "config/reco.config.json"


def load_config(path: str) -> dict:
    """Load and return the reco.config.json file."""
    with open(path) as f:
        return json.load(f)


def get_source_conn(source_cfg: dict):
    """Connect to the client's source database."""
    return psycopg2.connect(
        dbname=source_cfg['dbname'],
        user=source_cfg['user'],
        password=source_cfg['password'],
        host=source_cfg['host'],
        port=source_cfg['port']
    )


def fetch_source_products(source_conn, table: str) -> tuple:
    """
    Read all products from the client's source table.
    Returns (rows, column_names).
    """
    cur = source_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    cur.close()
    return rows


def map_product(row: dict, mapping: dict, project_id: str) -> dict:
    """
    Map client column names to your items schema
    using the mapping defined in reco.config.json.
    """
    metadata = {}
    for field in mapping.get('metadata', []):
        value = row.get(field)
        # Convert Decimal to float for JSON serialization
        if isinstance(value, Decimal):
            value = float(value)
        # Convert list/array types
        elif hasattr(value, '__iter__') and not isinstance(value, str):
            value = list(value)
        metadata[field] = value

    return {
        'project_id':  project_id,
        'external_id': row.get(mapping['external_id']),
        'title':       row.get(mapping['title']),
        'description': row.get(mapping.get('description')),
        'category':    row.get(mapping.get('category')),
        'item_type':   mapping.get('item_type', 'product'),
        'metadata':    json.dumps(metadata)
    }


def upsert_item(cur, item: dict):
    """
    Insert or update a single item in the items table.
    ON CONFLICT updates existing rows so catalog stays fresh.
    """
    cur.execute("""
        INSERT INTO items (
            project_id, external_id, item_type,
            title, description, category, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (project_id, external_id)
        DO UPDATE SET
            title       = EXCLUDED.title,
            description = EXCLUDED.description,
            category    = EXCLUDED.category,
            metadata    = EXCLUDED.metadata,
            updated_at  = now()
    """, (
        item['project_id'],
        item['external_id'],
        item['item_type'],
        item['title'],
        item['description'],
        item['category'],
        item['metadata']
    ))


def sync_catalog(config_path: str = CONFIG_PATH):
    """
    Main sync function:
    1. Load config
    2. Connect to client source DB
    3. Fetch all products
    4. Map each product to items schema
    5. Upsert into items table
    """
    print("\n--- Catalog sync started ---\n")

    # Step 1 — load config
    config     = load_config(config_path)
    project_id = config['project_id']
    mapping    = config['mapping']
    source_cfg = config['source']
    table      = source_cfg['table']

    print(f"  Project  : {project_id}")
    print(f"  Source   : {source_cfg['dbname']}.{table}")
    print(f"  Target   : ingestion_db.items\n")

    # Step 2 — connect to client source DB
    source_conn = get_source_conn(source_cfg)

    # Step 3 — fetch all products from client DB
    rows = fetch_source_products(source_conn, table)
    source_conn.close()

    if not rows:
        print("  No products found in source table.")
        return

    print(f"  Found {len(rows)} product(s) in source. Syncing...\n")

    # Step 4 — connect to ingestion_db and upsert
    dst_conn = get_conn()
    dst_conn.cursor_factory = psycopg2.extras.RealDictCursor
    cur = dst_conn.cursor()

    synced  = 0
    failed  = 0

    for row in rows:
        try:
            item = map_product(row, mapping, project_id)
            upsert_item(cur, item)
            synced += 1
            print(f"  ✓  Synced | external_id={item['external_id']:12} | "
                  f"title={item['title']}")
        except Exception as e:
            failed += 1
            print(f"  ✗  Failed | external_id={row.get(mapping['external_id'])} | {e}")

    # One commit for all upserts
    dst_conn.commit()
    cur.close()
    dst_conn.close()

    # Summary
    print(f"""
  ── Summary ──────────────────────────
  ✓  Synced  : {synced}
  ✗  Failed  : {failed}
  ─────────────────────────────────────
    """)


if __name__ == "__main__":
    sync_catalog()