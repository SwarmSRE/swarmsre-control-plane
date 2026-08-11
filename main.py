from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import incidents, websockets

app = FastAPI(
    title="SwarmSRE Control Plane",
    description="The brain of the operation for predicting, detecting, and fixing K8s incidents.",
    version="1.0.0",
)

# Allow CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://swarmsre.app",
        "https://www.swarmsre.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router)
app.include_router(websockets.router)

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for the control plane."""
    return {"status": "ok", "component": "control-plane"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
