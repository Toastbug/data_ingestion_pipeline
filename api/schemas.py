# api/schemas.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, timezone


ALLOWED_EVENT_TYPES = [
    'view', 'click', 'scroll_75', 'add_to_cart', 'wishlist',
    'video_finish', 'article_read', 'purchase', 'hide',
    'not_interested', 'return'
]

ALLOWED_ITEM_TYPES = ['product', 'content']

ALLOWED_DEVICES = ['mobile', 'desktop', 'tablet']

EVENT_WEIGHTS = {
    'view':         1.0,
    'click':        2.0,
    'scroll_75':    1.5,
    'add_to_cart':  3.0,
    'wishlist':     2.5,
    'video_finish': 3.0,
    'article_read': 3.0,
    'purchase':     5.0,
    'hide':        -1.0,
    'not_interested': -1.0,
    'return':      -2.0
}


class EventRequest(BaseModel):
    project_id: str
    user_id:    str
    item_id:    str
    item_type:  str
    event_type: str
    session_id: str
    device:     str
    timestamp:  Optional[datetime] = None
    context:    Optional[dict]     = {}

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        if v not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"event_type '{v}' is not allowed. "
                             f"Must be one of: {ALLOWED_EVENT_TYPES}")
        return v

    @field_validator('item_type')
    @classmethod
    def validate_item_type(cls, v):
        if v not in ALLOWED_ITEM_TYPES:
            raise ValueError(f"item_type '{v}' is not allowed. "
                             f"Must be one of: {ALLOWED_ITEM_TYPES}")
        return v

    @field_validator('device')
    @classmethod
    def validate_device(cls, v):
        if v not in ALLOWED_DEVICES:
            raise ValueError(f"device '{v}' is not allowed. "
                             f"Must be one of: {ALLOWED_DEVICES}")
        return v

    @field_validator('timestamp', mode='before')
    @classmethod
    def set_default_timestamp(cls, v):
        if v is None:
            return datetime.now(timezone.utc)
        return v


class EventResponse(BaseModel):
    status:  str
    msg_id:  int
    message: str