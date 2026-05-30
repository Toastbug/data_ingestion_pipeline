# api/routes.py
import json
import psycopg2
from fastapi import APIRouter, HTTPException
from api.schemas import EventRequest, EventResponse
from api.validators import validate_event
from db import get_conn

router = APIRouter()

QUEUE = 'events_queue'


@router.post("/events", response_model=EventResponse)
def receive_event(payload: EventRequest):
    """
    Single endpoint for all event types.
    1. Pydantic validates shape via EventRequest schema
    2. validators.py assigns weight and builds clean dict
    3. Event is enqueued into PGMQ
    4. Returns msg_id confirmation
    """

    # Step 1 — validate and build clean event dict
    try:
        event = validate_event(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Step 2 — enqueue into PGMQ
    conn = None
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute(
            "SELECT pgmq.send(%s, %s::jsonb)",
            (QUEUE, json.dumps(event))
        )

        msg_id = cur.fetchone()[0]
        conn.commit()
        cur.close()

        return EventResponse(
            status  = "queued",
            msg_id  = msg_id,
            message = f"Event '{event['event_type']}' queued successfully"
        )

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code = 500,
            detail      = f"Database error: {str(e)}"
        )

    finally:
        if conn:
            conn.close()


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    Confirms API is running and database is reachable.
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {
            "status":   "healthy",
            "database": "connected",
            "queue":    QUEUE
        }
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Database unreachable: {str(e)}"
        )