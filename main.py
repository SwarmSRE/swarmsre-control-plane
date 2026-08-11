import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import incidents, websockets

app = FastAPI(
    title="SwarmSRE Control Plane",
    description="The brain of the operation for predicting, detecting, and fixing K8s incidents.",
    version="1.0.0",
)

# Include API routers first (higher priority than static file catch-all)
app.include_router(incidents.router)
app.include_router(websockets.router)

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for the control plane."""
    return {"status": "ok", "component": "control-plane"}

# Serve the compiled React dashboard UI as static files (ArgoCD pattern)
# In production, the Dockerfile multi-stage build compiles the UI into ui/dist/
# In development, run `cd ui && npm run build` first, or use Vite dev server separately
UI_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.isdir(UI_DIR):
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
