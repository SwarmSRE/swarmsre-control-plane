import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from api import audit, incidents, metrics, topology, websockets
from core.watcher import watch_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the Kubernetes event watcher in the background
    task = asyncio.create_task(watch_events(incidents.on_incident_detected))
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

app = FastAPI(
    title="SwarmSRE Control Plane",
    description="The brain of the operation for predicting, detecting, and fixing K8s incidents.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routers first (higher priority than static file catch-all)
app.include_router(incidents.router)
app.include_router(websockets.router)
app.include_router(audit.router)
app.include_router(metrics.router)
app.include_router(topology.router)

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for the control plane."""
    return {"status": "ok", "component": "control-plane"}

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def handle_api_404(request: Request, path: str):
    """Explicitly return 404 for unknown /api/ routes so they don't fall through to the UI."""
    raise HTTPException(status_code=404, detail="API route not found")

# Serve the compiled React dashboard UI as static files (ArgoCD pattern)
# In production, the Dockerfile multi-stage build compiles the UI into ui/dist/
# In development, run `cd ui && npm run build` first, or use Vite dev server separately
UI_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.isdir(UI_DIR):
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
