from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil, json

from app.database import get_db
from app.services.withings_import import import_withings_csv, import_garmin_csv
from app.services.blood_pdf_parser import scan_folder_for_new_pdfs
from app.services.bulk_import import import_all, import_withings_all, import_garmin_all, import_mfp_all
from app.models import DailyLog

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
IMPORTS_DIR = BASE_DIR / "data" / "Imports"

WITHINGS_DIR = BASE_DIR / "Imports" / "Withings"
GARMIN_DIR   = BASE_DIR / "Imports" / "Garmin" / "DI_CONNECT" / "DI-Connect-Wellness"
MFP_DIR      = BASE_DIR / "Imports" / "Myfitnesspal"


@router.get("/", include_in_schema=False)
async def imports_overview(request: Request, msg: str = None, db: Session = Depends(get_db)):
    # Status der Ordner prüfen
    withings_ok = WITHINGS_DIR.exists()
    garmin_ok   = GARMIN_DIR.exists()
    mfp_ok      = MFP_DIR.exists()

    # Anzahl vorhandener Tages-Logs
    total_logs = db.query(DailyLog).count()

    return templates.TemplateResponse("imports.html", {
        "request": request,
        "msg": msg,
        "withings_ok": withings_ok,
        "garmin_ok": garmin_ok,
        "mfp_ok": mfp_ok,
        "total_logs": total_logs,
        "withings_dir": str(WITHINGS_DIR),
        "garmin_dir": str(GARMIN_DIR),
        "mfp_dir": str(MFP_DIR),
    })


# ─── Bulk-Import (alles auf einmal) ──────────────────────────────────────────

@router.post("/alles", include_in_schema=False)
async def import_everything(db: Session = Depends(get_db)):
    results = import_all(db)
    w = results.get("withings", {})
    g = results.get("garmin", {})
    m = results.get("mfp", {})
    total = results.get("total_daily_logs", 0)

    parts = []
    if isinstance(w, dict) and not w.get("error"):
        parts.append(f"Withings: {w.get('weight',0)} Gewichts-Eintraege")
    if isinstance(g, dict) and not g.get("error"):
        parts.append(f"Garmin: {g.get('health',0)} Gesundheits-Tage + {g.get('sleep',0)} Schlaf-Tage")
    if isinstance(m, dict) and not m.get("error"):
        parts.append(f"MFP: {m.get('days',0)} Ernaehrungs-Tage")

    errors = (w.get("errors",[]) if isinstance(w,dict) else []) + \
             (g.get("errors",[]) if isinstance(g,dict) else []) + \
             (m.get("errors",[]) if isinstance(m,dict) else [])

    msg = " | ".join(parts) + f" | Gesamt {total} Tages-Logs in DB"
    if errors:
        msg += f" | {len(errors)} Fehler (Details im Server-Log)"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/withings-bulk", include_in_schema=False)
async def import_withings_bulk(db: Session = Depends(get_db)):
    stats = import_withings_all(db)
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    else:
        msg = f"Withings: {stats.get('weight',0)} Gewichts-Eintraege, {stats.get('steps',0)} Schritte-Tage importiert"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/garmin-bulk", include_in_schema=False)
async def import_garmin_bulk(db: Session = Depends(get_db)):
    stats = import_garmin_all(db)
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    else:
        msg = f"Garmin: {stats.get('health',0)} Gesundheitstage + {stats.get('sleep',0)} Schlaftage importiert"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/mfp-bulk", include_in_schema=False)
async def import_mfp_bulk(db: Session = Depends(get_db)):
    stats = import_mfp_all(db)
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    else:
        msg = f"MyFitnessPal: {stats.get('days',0)} Tage ({stats.get('rows',0)} Mahlzeiten) importiert"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


# ─── Einzeldatei-Upload (Fallback) ───────────────────────────────────────────

@router.post("/withings", include_in_schema=False)
async def import_withings_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dest = IMPORTS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    stats = import_withings_csv(dest, db)
    msg = f"Withings (Einzeldatei): {stats.get('imported',0)} neu, {stats.get('updated',0)} aktualisiert"
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/garmin", include_in_schema=False)
async def import_garmin_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dest = IMPORTS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    stats = import_garmin_csv(dest, db)
    msg = f"Garmin (Einzeldatei): {stats.get('imported',0)} neu, {stats.get('updated',0)} aktualisiert"
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/blutbilder-scan", include_in_schema=False)
async def scan_blutbilder(db: Session = Depends(get_db)):
    new_panels = scan_folder_for_new_pdfs(db)
    msg = f"{len(new_panels)} neue Blutbild-PDF(s) geparst"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)
