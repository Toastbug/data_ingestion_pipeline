# api/main.py
from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title       = "Aice Reco Ingestion API",
    description = "Receives events from the SDK and enqueues them into PGMQ",
    version     = "1.0.0"
)

# Register routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    print("\n--- Ingestion API started ---")
    print("  POST /api/v1/events  → receive events")
    print("  GET  /api/v1/health  → health check")
    print("  GET  /docs           → auto API docs\n")


@app.on_event("shutdown")
def on_shutdown():
    print("\n--- Ingestion API stopped ---\n")