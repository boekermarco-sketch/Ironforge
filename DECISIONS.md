# DECISIONS.md – Architektur- und Entscheidungsprotokoll

Stand: 01.04.2026 | Version 1.0

---

## 1. Datenbankwahl: SQLite statt PostgreSQL

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Lokale Single-User-Anwendung auf Windows-PC.
- **Entscheidung:** SQLite mit SQLAlchemy ORM.
- **Begründung:** Kein separater DB-Server nötig, Zero-Config, `fitness.db`-Datei ist direkt portierbar.
- **Alternativen:** PostgreSQL (zu viel Overhead für Single-User), JSON-Dateien (keine Relations).
- **Trade-offs:** Keine Concurrent-Writes (kein Problem bei Single-User), keine Full-Text-Search.
- **Migration:** Das SQLAlchemy-Modell ist PostgreSQL-kompatibel – Umstieg jederzeit möglich.

---

## 2. Server-Side Rendering statt React/Vue

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Marco hat keine Programmierkenntnisse, will vollständig lauffähigen Code.
- **Entscheidung:** Jinja2-Templates mit FastAPI, Chart.js via CDN.
- **Begründung:** Kein Build-Prozess (npm, webpack etc.), einfach zu warten, sofort verständlich.
- **Alternativen:** React SPA + FastAPI REST (zu komplex), HTMX (guter Mittelweg, aber Lernkurve).
- **Trade-offs:** Kein reaktives UI, vollständige Page-Reloads bei Formularen.

---

## 3. dose_events als Zeitreihe (nie überschreiben)

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Dosierungsänderungen müssen historisch nachvollziehbar sein für Korrelationsanalysen.
- **Entscheidung:** Jede Dosisänderung = neuer Eintrag mit `start_date`. Altes Ende via `end_date` schließen.
- **Begründung:** Nur so lässt sich rekonstruieren, welche Dosis zum Zeitpunkt eines Blutbilds aktiv war.
- **Alternativen:** UPDATE bestehenden Eintrag (Verlust der Historie), separate Changelog-Tabelle (redundant).
- **Trade-offs:** Mehr Zeilen in DB, Query für "aktive Dosis" etwas komplexer.

---

## 4. PDF-Parser: pdfplumber statt PyMuPDF/OCR

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Deutsche Labor-PDFs sind fast immer Text-PDFs (kein Scan).
- **Entscheidung:** pdfplumber für Textextraktion + Regex für Wert-Erkennung.
- **Begründung:** Beste Textqualität bei deutschen PDFs, keine OCR-Abhängigkeit nötig.
- **Alternativen:** PyMuPDF (schneller aber schlechtere Tabellenextraktion), Tesseract-OCR (nur für Scans).
- **Trade-offs:** Funktioniert nicht bei Foto-PDFs/Scans → geplant: Phase 3 OCR-Fallback.
- **Alias-System:** Jeder Biomarker hat `aliases`-Feld – Erweiterbar ohne Code-Änderung.

---

## 5. Konsultations-Journal als eigenes Modul

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Claude-Chat-Verläufe gehen verloren. Analysen sollen dauerhaft gespeichert werden.
- **Entscheidung:** `journal_entries`-Tabelle mit Datum, Bild-Pfad, Analyse-Text, Tags.
- **Begründung:** Fotos + KI-Meinungen chronologisch blätterbar, filterbar nach Typ.
- **Geplante Erweiterung Phase 3:** Claude-API-Integration → automatische Speicherung beim Analysieren.
- **Trade-offs:** Aktuell manuelles Copy-Paste der Claude-Analyse nötig.

---

## 6. Seed-Daten beim ersten Start

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Marco will sofort mit vorausgefüllten Daten starten (Stack, Blutbilder, Garmin-Verlauf).
- **Entscheidung:** `seed_data.py` läuft beim App-Start, prüft ob DB leer, füllt bei Bedarf.
- **Begründung:** Kein manuelles Datenbankscript, kein SQL-Wissen nötig.
- **Trade-offs:** DB-Reset (fitness.db löschen) lädt alle Seed-Daten neu – manuell eingegebene Daten gehen verloren.

---

## 7. Aderlass / Blutspende als wählbarer Typ

- **Datum:** 01.04.2026
- **Status:** Accepted
- **Kontext:** Marco macht Aderlass (therapeutisch, kein gespendetes Blut) und will auch Blutspende separat tracken können.
- **Entscheidung:** `medical_events.event_type` als freier String mit Vorschlagswerten: Aderlass / Blutspende / Arzttermin / Sonstiges.
- **Begründung:** Beide Ereignisse relevant für Hämatokrit-Verlauf, unterschiedliche medizinische Bedeutung.
- **Seed-Daten:** Aderlass 30.03.2026 (450ml, Blutspendezentrum Bremen) bereits eingetragen.

---

## Offen / Noch nicht entschieden

| Frage | Optionen | Status |
|---|---|---|
| Claude API-Key-Management | Env-Variable vs. Datei vs. UI-Eingabe | Offen (Phase 3) |
| Garmin API vs. CSV | API braucht OAuth, CSV ist einfacher | CSV für Phase 1+2 |
| Withings API | Vorhanden, braucht App-Registrierung | CSV für Phase 1+2 |
| Backup-Strategie | fitness.db regelmäßig kopieren | Noch nicht implementiert |
