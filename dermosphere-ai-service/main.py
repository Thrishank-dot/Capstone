import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import router from Step 1 file (e.g., triage_router.py)
from api import router as triage_router, STATIC_DIR

app = FastAPI(title="DermoSphere AI Service Engine")

# Configure CORS for Spring Boot & Client UI Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /static directory so heatmap images can be fetched via HTTP
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount Triage Router (/api/v1/triage)
app.include_router(triage_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)