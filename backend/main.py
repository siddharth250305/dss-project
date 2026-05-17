"""
Cargo-Aware Drone Selection DSS — FastAPI Application Entry Point.
Serves all REST API endpoints and seeds the database on startup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from seed_data import seed_database

from routers.drones import router as drones_router
from routers.missions import router as missions_router
from routers.cargo_zones import router as cargo_zones_router
from routers.environment import router as environment_router
from routers.decisions import router as decisions_router
from routers.settings import router as settings_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cargo-Aware Drone Selection DSS",
    description="Decision Support System for selecting the optimal drone for port cargo missions.",
    version="1.0.0",
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drones_router)
app.include_router(missions_router)
app.include_router(cargo_zones_router)
app.include_router(environment_router)
app.include_router(decisions_router)
app.include_router(settings_router)


@app.on_event("startup")
def startup_event():
    """Seed the database with sample data on first run."""
    seed_database()


@app.get("/")
def root():
    return {"message": "Cargo-Aware Drone Selection DSS API is running."}
