"""FastAPI server for Ortho context hub."""

from fastapi import FastAPI

app = FastAPI(title="Ortho API", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/search")
async def search(q: str = "") -> dict:
    """Search for artifacts."""
    if not q:
        return {"error": "query required"}
    return {"query": q, "results": []}


@app.post("/api/v1/artifacts")
async def create_artifact(name: str = "", content: str = "") -> dict:
    """Create a new artifact."""
    if not name or not content:
        return {"error": "name and content required"}
    return {"id": "artifact-001", "name": name, "created": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
