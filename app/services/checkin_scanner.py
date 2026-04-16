"""
Check-in Foto Scanner.
Scannt Imports/CheckIn_Fotos/<DD.MM.YYYY>/ nach neuen Bildern
und legt automatisch JournalEntries an.
Analyse erfolgt manuell über den Chat mit Claude.
"""
from pathlib import Path
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models import JournalEntry

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHECKIN_DIR = BASE_DIR / "Imports" / "CheckIn_Fotos"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _parse_folder_date(name: str):
    """Parst DD.MM.YYYY oder YYYY-MM-DD aus dem Ordnernamen."""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(name.strip(), fmt).date()
        except ValueError:
            continue
    return None


def scan_checkin_folder(db: Session) -> list[JournalEntry]:
    """Scannt CHECKIN_DIR nach neuen Fotos und legt JournalEntries an."""
    if not CHECKIN_DIR.exists():
        return []

    existing_paths = {
        e.image_path
        for e in db.query(JournalEntry.image_path)
                    .filter(JournalEntry.entry_type == "Check-in")
                    .all()
        if e.image_path
    }

    new_entries = []

    for folder in sorted(CHECKIN_DIR.iterdir()):
        if not folder.is_dir():
            continue
        folder_date = _parse_folder_date(folder.name)
        if not folder_date:
            continue

        images = sorted(
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_SUFFIXES
        )

        for img in images:
            rel_path = f"CheckIn_Fotos/{folder.name}/{img.name}"
            if rel_path in existing_paths:
                continue
            entry = JournalEntry(
                date=folder_date,
                title=f"Check-in {folder.name}",
                entry_type="Check-in",
                image_path=rel_path,
                analysis_text="",
            )
            db.add(entry)
            new_entries.append(entry)

    if new_entries:
        db.commit()
        for e in new_entries:
            db.refresh(e)

    return new_entries


def get_all_checkins(db: Session) -> dict[date, list[JournalEntry]]:
    """Gibt alle Check-in Einträge als Dict {date: [entries]} zurück, neueste zuerst."""
    scan_checkin_folder(db)

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.entry_type == "Check-in")
        .order_by(JournalEntry.date.desc(), JournalEntry.id.asc())
        .all()
    )

    grouped: dict[date, list[JournalEntry]] = {}
    for e in entries:
        grouped.setdefault(e.date, []).append(e)

    return grouped
