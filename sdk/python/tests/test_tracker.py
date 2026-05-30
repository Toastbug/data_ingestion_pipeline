# tests/test_tracker.py
from aice_reco import RecoTracker
from aice_reco.exceptions import ValidationError, ConfigurationError

# ── Test 1 — initialize tracker ───────────────────────────
print("\n--- Test 1: Initialize tracker ---\n")
tracker = RecoTracker(
    api_key    = "test-api-key",
    project_id = "shop-x",
    api_url    = "http://localhost:8000/api/v1",
    device     = "desktop"
)

# ── Test 2 — ping API ─────────────────────────────────────
print("\n--- Test 2: Ping API ---\n")
health = tracker.ping()
print(f"  API status: {health}")

# ── Test 3 — track without identifying user ───────────────
print("\n--- Test 3: Track without user (should raise error) ---\n")
try:
    tracker.view('prod_001', 'product')
except ValidationError as e:
    print(f"  Caught expected error: {e}")

# ── Test 4 — identify user ────────────────────────────────
print("\n--- Test 4: Identify user ---\n")
tracker.identify('usr_001')

# ── Test 5 — track all event types ───────────────────────
print("\n--- Test 5: Track all event types ---\n")
tracker.view('prod_001', 'product', {'page': 'homepage'})
tracker.click('prod_001', 'product')
tracker.add_to_cart('prod_001', 'product')
tracker.wishlist('prod_002', 'product')
tracker.purchase('prod_001', 'product', {'referrer': 'recommendation'})
tracker.hide('prod_003', 'product')
tracker.not_interested('prod_003', 'product')

# ── Test 6 — track unknown item (goes to pending) ─────────
print("\n--- Test 6: Track unknown item (goes to pending_events) ---\n")
tracker.view('prod_unknown', 'product')

# ── Test 7 — wrong config (should raise error) ────────────
print("\n--- Test 7: Missing api_key (should raise error) ---\n")
try:
    bad_tracker = RecoTracker(
        api_key    = "",
        project_id = "shop-x",
        api_url    = "http://localhost:8000/api/v1"
    )
except ConfigurationError as e:
    print(f"  Caught expected error: {e}")

print("\n--- All tests done ---\n")