from __future__ import annotations

import sqlite3
from pathlib import Path


TOP_EQUIPMENT_ROWS = [
    # Brust
    ("Matrix", "Brust", "Ultra Chest Press", "https://de.matrixfitness.com/deu/strength/catalog/ultra-chest-press.jpg", "Konvergierend"),
    ("gym80", "Brust", "PURE KRAFT Chest Press", "https://gym80.de/produkte/pure-kraft-chest-press.jpg", "Duale Kraftuebertragung"),
    ("EGYM", "Brust", "Smart Strength Chest Press", "https://de.egym.com/de/workouts/smartstrength-chest.jpg", "Digitaler Widerstand"),
    # Ruecken
    ("Matrix", "Rücken", "Versa Lat Pulldown", "https://de.matrixfitness.com/deu/strength/catalog/versa-lat-pulldown.jpg", "Isolateral"),
    ("gym80", "Rücken", "Sygnum Dual Latzug", "https://gym80.de/produkte/sygnum-latzug.jpg", "Kugelgelagert"),
    ("EGYM", "Rücken", "Smart Strength Lat Pulldown", "https://de.egym.com/de/workouts/smartstrength-lat.jpg", "Automatische Einstellung"),
    ("Matrix", "Rücken", "Ultra Seated Row", "https://de.matrixfitness.com/deu/strength/catalog/ultra-seated-row.jpg", "Mehrfachgriff-Positionen"),
    ("gym80", "Rücken", "PURE KRAFT Low Row", "https://gym80.de/produkte/pure-kraft-low-row.jpg", "Plate Loaded"),
    ("EGYM", "Rücken", "Smart Strength Seated Row", "https://de.egym.com/de/workouts/smartstrength-row.jpg", "Ruderzug digital"),
    # Beine
    ("Matrix", "Beine", "Magnum 45° Leg Press", "https://de.matrixfitness.com/deu/strength/catalog/magnum-leg-press.jpg", "Linearfuehrung"),
    ("gym80", "Beine", "80CORE Beinpresse", "https://gym80.de/produkte/80core-legpress.jpg", "Kompaktbauweise"),
    ("EGYM", "Beine", "Smart Strength Leg Press", "https://de.egym.com/de/workouts/smartstrength-legpress.jpg", "Kraftmess-Modus"),
    ("Matrix", "Beine", "Ultra Leg Extension", "https://de.matrixfitness.com/deu/strength/catalog/ultra-leg-extension.jpg", "Beinstrecker"),
    ("gym80", "Beine", "Sygnum Beinstrecker", "https://gym80.de/produkte/sygnum-beinstrecker.jpg", "Klassisch mechanisch"),
    # Schultern
    ("Matrix", "Schultern", "Ultra Shoulder Press", "https://de.matrixfitness.com/deu/strength/catalog/ultra-shoulder-press.jpg", "Gegengewichts-System"),
    ("gym80", "Schultern", "PURE KRAFT Shoulder Press", "https://gym80.de/produkte/pure-kraft-shoulder-press.jpg", "Konvergierend"),
    ("EGYM", "Schultern", "Smart Strength Shoulder Press", "https://de.egym.com/de/workouts/smartstrength-shoulder.jpg", "Elektrisch unterstuetzt"),
    # Arme
    ("Matrix", "Arme", "Versa Biceps Curl", "https://de.matrixfitness.com/deu/strength/catalog/versa-bicep.jpg", "Ergonomische Griffe"),
    ("gym80", "Arme", "Sygnum Scott-Curl", "https://gym80.de/produkte/sygnum-scott-curl.jpg", "Optimale Isolation"),
    ("EGYM", "Arme", "Smart Strength Bicep Curl", "https://de.egym.com/de/workouts/smartstrength-bicep.jpg", "Echtzeit-Biofeedback"),
]


def seed_training_equipment(db_path: Path) -> dict:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                category TEXT NOT NULL,
                equipment_name TEXT NOT NULL,
                image_url TEXT,
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_training_equipment_unique
            ON training_equipment(brand, category, equipment_name)
            """
        )
        before = conn.execute("SELECT COUNT(*) FROM training_equipment").fetchone()[0]
        conn.executemany(
            """
            INSERT OR IGNORE INTO training_equipment
                (brand, category, equipment_name, image_url, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            TOP_EQUIPMENT_ROWS,
        )
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM training_equipment").fetchone()[0]
        return {"ok": True, "before": before, "after": after, "inserted": max(0, after - before)}
    finally:
        conn.close()
