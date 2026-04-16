from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.database import engine, Base
from app.routers import dashboard, stack, blood, daily_log, events, journal, imports, checkin

# Alle Tabellen anlegen (beim ersten Start)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fitness Dashboard – Marco Böker",
    description="Persönliches Gesundheits- und Protokoll-Dashboard",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/data", StaticFiles(directory=BASE_DIR / "data"), name="data")
app.mount("/imports", StaticFiles(directory=BASE_DIR / "Imports"), name="imports")

# Router registrieren
app.include_router(dashboard.router)
app.include_router(stack.router, prefix="/stack", tags=["Stack"])
app.include_router(blood.router, prefix="/blutbilder", tags=["Blutbilder"])
app.include_router(daily_log.router, prefix="/tageslog", tags=["Tageslog"])
app.include_router(events.router, prefix="/ereignisse", tags=["Ereignisse"])
app.include_router(journal.router, prefix="/journal", tags=["Journal"])
app.include_router(imports.router, prefix="/import", tags=["Import"])
app.include_router(checkin.router, prefix="/checkin", tags=["CheckIn"])


def _run_migrations():
    """Fügt neue Spalten zur daily_logs Tabelle hinzu ohne Datenverlust."""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    existing = [c["name"] for c in inspector.get_columns("daily_logs")]
    new_cols = {
        "fat_mass_kg": "FLOAT",
        "water_percent": "FLOAT",
        "bp_systolic": "INTEGER",
        "bp_diastolic": "INTEGER",
        "vascular_age": "INTEGER",
        "pulse_wave_velocity": "FLOAT",
        "light_sleep_min": "INTEGER",
        "training_readiness": "INTEGER",
        "training_status": "VARCHAR(100)",
        "bmi": "FLOAT",
        "muscle_mass": "FLOAT",
        "stress_avg": "INTEGER",
        "vo2max": "FLOAT",
    }
    with engine.connect() as conn:
        for col, col_type in new_cols.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE daily_logs ADD COLUMN {col} {col_type}"))
        conn.commit()


_run_migrations()


@app.on_event("startup")
async def startup_event():
    """Seed-Daten laden wenn DB leer; Stack-Updates anwenden."""
    from app.database import SessionLocal
    from app.services.seed_data import seed_all
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
