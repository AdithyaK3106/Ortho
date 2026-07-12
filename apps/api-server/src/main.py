"""FastAPI server for Ortho — unified API + orchestration."""

from fastapi import FastAPI
from routers.orchestration import router as orchestration_router

app = FastAPI(title="Ortho API", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# Include orchestration endpoints (task-013: /run, /approve, /reject, /status, /history)
app.include_router(orchestration_router)


if __name__ == "__main__":
    import uvicorn
    # Local-first, no auth (CLAUDE.md key decision 4) — never bind beyond loopback
    uvicorn.run(app, host="127.0.0.1", port=8000)
