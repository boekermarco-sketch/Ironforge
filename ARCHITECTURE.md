# ARCHITECTURE.md – Fitness Dashboard Marco Böker

Stand: 01.04.2026 | Version 1.0

---

## 1. Übersicht

**Zweck:** Persönliches Gesundheits- und Protokoll-Dashboard für Marco Böker.
Bündelt Daten aus Withings, Garmin, MyFitnessPal, manuelle Blutbilder, Stack-Protokolle und ein KI-Konsultationsjournal.

**Zielgruppe:** Einzelner privater Nutzer. Läuft lokal auf Windows-PC (localhost:8000).

**Kernfunktionen:**
- Stack-Verwaltung (Substanzen, Dosierungen, zeitbasierte Historisierung)
- Blutbild-Erfassung (PDF-Parser für deutsche Labore + manuelle Eingabe)
- Tageslog (Garmin-Metriken, Withings-Körperdaten, subjektive Werte)
- Konsultations-Journal (Fotos, KI-Analysen, chronologische Timeline)
- Medizinische Ereignisse (Aderlass, Blutspende, Arzttermin)
- Import-Pipeline (Withings CSV, Garmin CSV, Blutbild-PDFs)
- Charts & Verlaufsanalysen (Chart.js)

---

## 2. Technischer Stack

| Komponente | Technologie | Begründung |
|---|---|---|
| Backend | Python 3.13 + FastAPI | Schnell, async-fähig, SQLAlchemy-Integration |
| Datenbank | SQLite (fitness.db) | Lokal, kein Server nötig, einfach |
| ORM | SQLAlchemy 2.x | Typsichere Modelle, einfache Queries |
| Templates | Jinja2 (Server-Side Rendering) | Kein JS-Framework nötig, einfach zu warten |
| Charts | Chart.js (CDN) | Keine Installation, reichhaltig |
| PDF-Parser | pdfplumber | Beste Textextraktion für deutsche Lab-PDFs |
| Styling | Custom CSS (hellgrün, --green-*) | Maßgeschneidert, keine externe Abhängigkeit |
| Hosting | uvicorn (localhost:8000) | Einfach, kein Cloud-Setup |

---

## 3. Architektur-Übersicht

```
Browser (http://localhost:8000)
        ↓ HTTP GET/POST
FastAPI (app/main.py)
        ↓ Jinja2 Templates
        ↓ SQLAlchemy ORM
SQLite (fitness.db)
        ↑
Services (PDF-Parser, CSV-Import, Seed-Daten)
        ↑
data/Blutbilder/    ← PDFs hier ablegen
data/Fortschritt_Fotos/ ← Fotos hier ablegen
data/Imports/       ← CSV-Dateien hier ablegen
```

**Schichtenmodell:**
1. **Templates** – Jinja2 HTML-Seiten, rein darstellend
2. **Router** – FastAPI-Routen, HTTP-Handler, minimale Logik
3. **Services** – Geschäftslogik (PDF-Parser, CSV-Import, Seed-Daten)
4. **Models** – SQLAlchemy ORM-Tabellen
5. **Database** – SQLite-Verbindung, Session-Management

---

## 4. Modulgrenzen & Verantwortlichkeiten

| Modul | Datei(en) | Verantwortung |
|---|---|---|
| Stack | routers/stack.py | Substanzen, Dosierungen, Stack-CRUD |
| Blutbilder | routers/blood.py | Blutbild-CRUD, PDF-Upload-Trigger, Chart-API |
| Tageslog | routers/daily_log.py | Garmin/Withings/manuelle Tagesdaten |
| Journal | routers/journal.py | KI-Analysen, Fotos, Timeline |
| Ereignisse | routers/events.py | Aderlass, Blutspende, Arzttermin |
| Import | routers/imports.py | CSV-Upload-Handler |
| Dashboard | routers/dashboard.py | Übersichtsseite, aggregierte Daten |
| PDF-Parser | services/blood_pdf_parser.py | pdfplumber + Regex + Alias-Matching |
| CSV-Import | services/withings_import.py | Withings + Garmin CSV |
| Seed-Daten | services/seed_data.py | Marcos Stack vorausgefüllt beim Erststart |

---

## 5. Datenmodell (Kern-Tabellen)

```
substances          → Substanz-Stammdaten (Name, Kategorie, Route)
stacks              → Protokoll/Zyklus (Blast, Cruise)
dose_events         → Dosierungshistorie (NIEMALS überschreiben, immer neue Zeile)
biomarkers          → Labor-Marker-Stammdaten + Referenzbereiche
blood_panels        → Eine Blutabnahme (Datum, Labor)
blood_values        → Einzelwerte pro Panel + Ampel-Status
daily_logs          → Tagesmetriken (Garmin + Withings + subjektiv + Ernährung)
medical_events      → Aderlass, Blutspende, Arzttermin
journal_entries     → Chronologisches Journal (Foto + Analyse + Tags)
```

**Kritisches Design-Prinzip:** `dose_events` wird NIEMALS überschrieben.
Jede Dosisänderung ist ein neuer Eintrag mit `start_date`. Nur so sind
spätere Korrelationen (Dosis ↔ Blutwerte) korrekt nachvollziehbar.

---

## 6. Blutbild-PDF-Parser

**Datei:** `app/services/blood_pdf_parser.py`

**Funktionsweise:**
1. Öffnet PDF mit pdfplumber (Text-PDF, kein OCR)
2. Extrahiert Datum aus erstem Datums-Pattern
3. Für jede Zeile: sucht bekannte Biomarker-Namen via Alias-Map
4. Extrahiert Zahlenwert + Referenzbereich + Einheit via Regex
5. Erstellt BloodPanel + BloodValues in DB
6. Erkennt aktiven Stack zum Datum automatisch

**Einschränkung:** Funktioniert nur mit Text-PDFs (Standard bei deutschen Laboren).
Scans/Foto-PDFs erfordern OCR (geplant Phase 3).

**Alias-System:** Jeder Biomarker hat ein `aliases`-Feld (kommagetrennt).
Parser prüft alle Aliases, bevorzugt längste Übereinstimmung.

---

## 7. Konsultations-Journal

**Zweck:** Dauerhafter Ersatz für vergängliche Claude-Chat-Verläufe.
Alles was in Claude besprochen wird (Analyse, Empfehlung, Foto-Bewertung)
soll hier mit Datum, Bild und Text gespeichert werden.

**Workflow:**
1. In Claude-Chat: Foto hochladen, Analyse erhalten
2. In Dashboard → Journal → Neuer Eintrag
3. Analyse-Text einfügen, Bild hochladen, Typ wählen
4. Wird dauerhaft in `journal_entries` gespeichert + chronologisch angezeigt

**Geplant (Phase 3):** Direkte Claude-API-Integration, damit Analyse automatisch gespeichert wird.

---

## 8. Datenfluss – typische Abläufe

**Blutbild-PDF (heute, 01.04.2026):**
```
PDF in data/Blutbilder/ legen
→ Import-Seite → "Ordner scannen"
→ blood_pdf_parser.py → pdfplumber → Regex
→ BloodPanel + BloodValues in DB
→ Redirect zu /blutbilder/{id}
→ Ampel-Farben sofort sichtbar
```

**Freitag Check-in:**
```
Garmin-App → Werte ablesen
→ /tageslog/ → Formular ausfüllen
→ DailyLog in DB
→ Charts aktualisieren sich automatisch
→ Journal-Eintrag mit Analyse anlegen
```

**Withings CSV-Import:**
```
account.withings.com → ZIP herunterladen
→ CSV aus ZIP → Import-Seite hochladen
→ withings_import.py → CSV parsen
→ DailyLog-Einträge erstellt/aktualisiert
→ Gewichtsverlauf im Dashboard sichtbar
```

---

## 9. Bekannte Einschränkungen & offene Punkte

| Punkt | Status | Geplant |
|---|---|---|
| OCR für Foto-PDFs | ❌ Noch nicht | Phase 3 |
| Claude-API-Integration für auto. Analyse | ❌ Noch nicht | Phase 3 |
| MyFitnessPal-Import | ❌ Noch nicht | Phase 2 |
| Automatischer Garmin-API-Sync | ❌ Noch nicht | Phase 3 |
| Pharmakokinetik-Charts | ❌ Noch nicht | Phase 3 |
| Symptom-Korrelations-Matrix | ❌ Noch nicht | Phase 3 |
| Multi-User / Hosting | ❌ Nicht vorgesehen | Optional |
| Blutbild-Panel Wert-Edit | ⚠️ Nur Hinzufügen | Phase 2 |

---

## 10. Wartungshinweise

- **Neue Biomarker:** In `services/seed_data.py` → `_seed_biomarkers()` ergänzen
- **Neue Stack-Substanzen:** Im Dashboard → Stack → Substanz anlegen
- **Parser-Probleme:** `aliases`-Feld in `biomarkers`-Tabelle erweitern (SQL oder Admin)
- **DB-Reset:** `fitness.db` löschen → beim Neustart werden Seed-Daten neu geladen
- **Port ändern:** In `start.bat` `--port 8000` anpassen
