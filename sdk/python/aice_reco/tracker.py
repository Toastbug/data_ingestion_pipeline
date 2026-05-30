# aice_reco/tracker.py
import uuid
from datetime import datetime, timezone
from aice_reco.api import APIClient
from aice_reco.exceptions import ConfigurationError, ValidationError


ALLOWED_EVENT_TYPES = [
    'view', 'click', 'scroll_75', 'add_to_cart', 'wishlist',
    'video_finish', 'article_read', 'purchase', 'hide',
    'not_interested', 'return'
]

ALLOWED_ITEM_TYPES = ['product', 'content']
ALLOWED_DEVICES    = ['mobile', 'desktop', 'tablet']


class RecoTracker:
    """
    Main SDK class. Clients instantiate this once
    and call its methods to track user events.

    Usage:
        tracker = RecoTracker(
            api_key    = 'your-api-key',
            project_id = 'shop-x',
            api_url    = 'http://localhost:8000/api/v1'
        )
        tracker.identify('usr_001')
        tracker.purchase('prod_abc', 'product')
    """

    def __init__(
        self,
        api_key:    str,
        project_id: str,
        api_url:    str  = 'http://localhost:8000/api/v1',
        device:     str  = 'desktop',
        timeout:    int  = 5
    ):
        # Validate config on init — fail early
        if not api_key:
            raise ConfigurationError("api_key is required")
        if not project_id:
            raise ConfigurationError("project_id is required")
        if not api_url:
            raise ConfigurationError("api_url is required")
        if device not in ALLOWED_DEVICES:
            raise ConfigurationError(
                f"device '{device}' is not allowed. "
                f"Must be one of: {ALLOWED_DEVICES}"
            )

        self.api_key    = api_key
        self.project_id = project_id
        self.device     = device
        self.user_id    = None
        self.session_id = str(uuid.uuid4())  # auto-generated per session

        # Internal API client
        self._client = APIClient(
            api_key = api_key,
            api_url = api_url,
            timeout = timeout
        )

        print(f"  RecoTracker initialized | project={project_id} | "
              f"session={self.session_id}")

    # ── Identity ──────────────────────────────────────────

    def identify(self, user_id: str):
        """
        Set the current user. Call this after login.
        All subsequent events will carry this user_id.
        """
        if not user_id:
            raise ValidationError("user_id cannot be empty")
        self.user_id = user_id
        print(f"  Identified user: {user_id}")

    # ── Event tracking methods ────────────────────────────

    def view(self, item_id: str, item_type: str, context: dict = {}):
        """User viewed an item."""
        return self._track('view', item_id, item_type, context)

    def click(self, item_id: str, item_type: str, context: dict = {}):
        """User clicked an item."""
        return self._track('click', item_id, item_type, context)

    def scroll_75(self, item_id: str, item_type: str, context: dict = {}):
        """User scrolled 75% of an item."""
        return self._track('scroll_75', item_id, item_type, context)

    def add_to_cart(self, item_id: str, item_type: str, context: dict = {}):
        """User added item to cart."""
        return self._track('add_to_cart', item_id, item_type, context)

    def wishlist(self, item_id: str, item_type: str, context: dict = {}):
        """User wishlisted an item."""
        return self._track('wishlist', item_id, item_type, context)

    def purchase(self, item_id: str, item_type: str, context: dict = {}):
        """User purchased an item."""
        return self._track('purchase', item_id, item_type, context)

    def hide(self, item_id: str, item_type: str, context: dict = {}):
        """User hid an item — negative signal."""
        return self._track('hide', item_id, item_type, context)

    def not_interested(self, item_id: str, item_type: str, context: dict = {}):
        """User marked not interested — negative signal."""
        return self._track('not_interested', item_id, item_type, context)

    def article_read(self, item_id: str, item_type: str, context: dict = {}):
        """User fully read an article."""
        return self._track('article_read', item_id, item_type, context)

    def video_finish(self, item_id: str, item_type: str, context: dict = {}):
        """User finished watching a video."""
        return self._track('video_finish', item_id, item_type, context)

    def returning(self, item_id: str, item_type: str, context: dict = {}):
        """User returned an item — negative signal."""
        return self._track('return', item_id, item_type, context)

    # ── Health check ──────────────────────────────────────

    def ping(self) -> dict:
        """
        Check if the API is reachable.
        Call this on startup to confirm connection.
        """
        return self._client.health_check()

    # ── Internal ──────────────────────────────────────────

    def _track(
        self,
        event_type: str,
        item_id:    str,
        item_type:  str,
        context:    dict = {}
    ) -> dict:
        """
        Internal method called by all public tracking methods.
        Validates, builds payload, sends to API.
        """

        # Must identify user before tracking
        if not self.user_id:
            raise ValidationError(
                "No user identified. Call tracker.identify(user_id) first."
            )

        # Validate item_type
        if item_type not in ALLOWED_ITEM_TYPES:
            raise ValidationError(
                f"item_type '{item_type}' is not allowed. "
                f"Must be one of: {ALLOWED_ITEM_TYPES}"
            )

        # Build payload
        payload = {
            "project_id": self.project_id,
            "user_id":    self.user_id,
            "item_id":    item_id,
            "item_type":  item_type,
            "event_type": event_type,
            "session_id": self.session_id,
            "device":     self.device,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "context":    context or {}
        }

        # Send to API
        response = self._client.send_event(payload)

        print(f"  Tracked | {event_type:12} | "
              f"item={item_id} | "
              f"msg_id={response.get('msg_id')}")

        return response