# api/validators.py
from api.schemas import EventRequest, EVENT_WEIGHTS
from datetime import datetime, timezone


def validate_event(event: EventRequest) -> dict:
    """
    Apply business logic validation on top of
    the Pydantic schema validation in schemas.py.
    Returns a clean dict ready to be enqueued.
    """

    # Assign weight automatically based on event_type
    weight = EVENT_WEIGHTS.get(event.event_type, 1.0)

    # Handle timestamp — use now() if not provided
    if event.timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    else:
        timestamp = event.timestamp.isoformat()

    # Build the clean event dict
    validated = {
        "project_id": event.project_id,
        "user_id":    event.user_id,
        "item_id":    event.item_id,
        "item_type":  event.item_type,
        "event_type": event.event_type,
        "weight":     weight,
        "session_id": event.session_id,
        "device":     event.device,
        "timestamp":  timestamp,
        "context":    event.context or {}
    }

    return validated