"""
Standalone-Script für den täglichen MFP-Abruf via Windows Task Scheduler.
Wird täglich um 23:00 ausgeführt – holt alle MFP-Daten seit dem letzten Abruf.

Aufruf:
  python run_mfp_fetch.py

Task Scheduler einrichten:
  setup_mfp_scheduler.bat ausführen (einmalig als Administrator)
"""
import sys
from pathlib import Path

# Projektpfad in sys.path aufnehmen
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from app.database import SessionLocal
from app.services.mfp_fetch import fetch_mfp_since_last


def main():
    db = SessionLocal()
    try:
        print("MFP-Abruf gestartet...")
        result = fetch_mfp_since_last(db)

        if result.get("error"):
            print(f"FEHLER: {result['error']}")
            sys.exit(1)

        fetched = result.get("fetched_dates", [])
        skipped = result.get("skipped", 0)
        errors  = result.get("errors", [])
        since   = result.get("since", "?")

        print(f"Seit: {since}")
        print(f"Importiert: {len(fetched)} Tag(e)" + (f" ({fetched[0]} – {fetched[-1]})" if fetched else ""))
        print(f"Übersprungen (keine Einträge): {skipped}")
        if errors:
            print(f"Fehler ({len(errors)}):")
            for e in errors:
                print(f"  {e}")
        print("MFP-Abruf abgeschlossen.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
