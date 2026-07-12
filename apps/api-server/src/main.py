"""FastAPI server for Ortho — unified health + orchestration API.

Note: Orchestration endpoints live in routers/orchestration.py but are
optional (only loaded if packages are available). Core health check always works.
"""

from fastapi import FastAPI

app = FastAPI(title="Ortho API", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint (always available)."""
    return {"status": "ok"}


# Orchestration router is optional
try:
    from routers.orchestration import router as orchestration_router
    app.include_router(orchestration_router)
except ImportError:
    # If orchestration packages not available, skip router
    # This allows API server to still run with just /health
    pass


if __name__ == "__main__":
    import uvicorn
    # Local-first, no auth (CLAUDE.md key decision 4) — never bind beyond loopback
    uvicorn.run(app, host="127.0.0.1", port=8000)
