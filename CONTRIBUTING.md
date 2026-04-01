# CONTRIBUTING.md – Wie weiterentwickelt werden kann

Stand: 01.04.2026 | Für Entwickler und KI-Assistenten

**Kontext:** Persönliches Gesundheits-Tool für Marco Böker (44J, Bremen).
Marco hat keine Programmierkenntnisse – Code muss vollständig lauffähig geliefert werden.
Wichtige Dateien: `ARCHITECTURE.md`, `DECISIONS.md`, `Übergabe_Protokoll.md`, `Stack_Marco.md`.

## Entwicklungsumgebung starten

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Oder: start.bat doppelklicken
```

## Projektstruktur (Kurzform)

```
app/main.py          ← FastAPI App + Router-Registrierung + Startup-Seed
app/database.py      ← SQLite fitness.db, Session-Factory
app/models.py        ← Alle SQLAlchemy-Tabellen (substances, stacks, dose_events, ...)
app/routers/         ← dashboard, stack, blood, daily_log, events, journal, imports
app/services/        ← seed_data, blood_pdf_parser, withings_import
templates/           ← Jinja2 HTML (base.html als Layout-Basis)
static/css/style.css ← Gesamtes Styling (hellgrünes Design, --green-*)
data/Blutbilder/     ← PDFs hier ablegen für automatischen Scan
data/Fortschritt_Fotos/ ← Fotos (über /data/ URL serviert)
data/Imports/        ← Temporäre CSV-Dateien
fitness.db           ← SQLite-Datenbank (auto-erstellt beim Start)
```

## Kritische Design-Regeln (NICHT ändern ohne Grund)

1. **dose_events werden NIEMALS überschrieben** – immer neuer Eintrag mit `start_date`
2. **Biomarker-Referenzbereiche** – immer Original-Laborreferenz in `blood_values.ref_min/max` speichern
3. **PDF-Parser ist defensiv** – lieber nichts als falschen Wert speichern
4. **DailyLog.source** – manuell / garmin / withings / gemischt (nie überschreiben mit schlechterer Quelle)
5. **Journal ist append-only** – Analyse-Texte nie überschreiben (historische Integrität)

## Neue Features hinzufügen

**Neue Seite:**
1. Router in `app/routers/neu.py` erstellen
2. In `app/main.py`: `app.include_router(neu.router, prefix="/neu")`
3. Template `templates/neu.html` (extends `base.html`)
4. Link in `templates/base.html` Navbar ergänzen

**Neuer Biomarker für PDF-Parser:**
In `services/seed_data.py` → `_seed_biomarkers()` ergänzen:
```python
{"name": "Marker Name", "unit": "mg/dL", "ref_min": 0.0, "ref_max": 100.0,
 "category": "Kategorie", "aliases": "Alias1,Alias2,englischer Name"},
```
Danach `fitness.db` löschen → App neu starten.

## Geplante Phase 2 / Phase 3 Features

**Phase 2:** MyFitnessPal CSV, Blutbild-Wert editieren, Verlaufstabelle Biomarker, Freitag Check-in Template-Seite
**Phase 3:** Claude API-Integration (auto. Analyse + Journal-Speicherung), Pharmakokinetik-Charts, OCR für Foto-PDFs, Garmin API-Sync, Warn-Logiken (Hämatokrit >52%), Symptom-Korrelations-Heatmap

---

Originales Beitragshandbuch unten:

---

Dieses Dokument beschreibt, wie Änderungen in dieses Projekt eingebracht werden sollen. Ziel ist eine konsistente, nachvollziehbare und qualitativ hochwertige Zusammenarbeit.

---

## 1. Grundprinzipien

Jede Änderung soll:

- sinnvoll begründet sein
- den bestehenden Projektstil respektieren
- sauber getestet sein
- dokumentiert werden
- den Scope nicht unnötig überschreiten

---

## 2. Vor jeder Änderung

Bevor du mit einer Änderung beginnst:

1. Lies die relevanten Dateien und die aktuelle Projektstruktur.
2. Prüfe, ob bereits bestehende Patterns oder Konventionen vorhanden sind.
3. Entscheide, ob es sich um Review, Refactor, Erweiterung oder Neuimplementierung handelt.
4. Kläre offene Fragen, bevor du großen Code umschreibst.

---

## 3. Kodierregeln

- Schreibe sauberen, modernen und modularen Code.
- Kleine, fokussierte Funktionen bevorzugen.
- Klare Benennungen verwenden.
- Keine unnötige Duplikation.
- Fehlende Fehlerbehandlung ergänzen.
- Sicherheit und Validierung mitdenken.
- Bestehende Strukturen nicht ohne Grund aufbrechen.
- Kommentare nur, wenn sie echten Mehrwert liefern.

---

## 4. Testanforderungen

Für neue oder geänderte Logik gilt:

- passende Tests hinzufügen oder aktualisieren
- Edge Cases prüfen
- kritische Pfade absichern
- bei fehlenden Tests die Lücke dokumentieren

Wenn ein Test nicht sinnvoll oder nicht möglich ist, muss das nachvollziehbar begründet werden.

---

## 5. Dokumentation

Bei relevanten Änderungen müssen gegebenenfalls aktualisiert werden:

- `README.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `REVIEW.md`
- In-Code-Dokumentation
- Inline-Kommentare, sofern nötig

Dokumentation soll kurz, klar und später wieder auffindbar sein.

---

## 6. Review-Prozess

Vor einem Merge oder einer finalen Übergabe sollte geprüft werden:

- Funktioniert die Änderung korrekt?
- Bleibt die Architektur konsistent?
- Ist die Änderung wartbar?
- Gibt es Sicherheits- oder Performance-Risiken?
- Sind Tests vorhanden oder sinnvoll ergänzt?
- Ist die Dokumentation aktuell?

---

## 7. Pull-Request-/Änderungsbeschreibung

Jede Änderung sollte eine kurze Beschreibung enthalten:

- Was wurde geändert?
- Warum wurde es geändert?
- Welche Dateien sind betroffen?
- Welche Tests wurden ausgeführt?
- Gibt es offene Punkte oder technische Schulden?

---

## 8. Empfehlungen für gute Beiträge

- Kleine, verständliche Änderungen bevorzugen.
- Große Umbauten in kleinere Schritte aufteilen.
- Vorhandene Architektur respektieren.
- Entscheidungen dokumentieren.
- Nicht nur Code, sondern auch Nachvollziehbarkeit liefern.

---

## 9. Commit-Hinweise

Wenn das Projekt Git verwendet, sind Commit-Nachrichten idealerweise:

- kurz
- konkret
- im Imperativ oder in sachlicher Form
- mit klar erkennbarem Inhalt

Beispiele:

- `Add input validation for user form`
- `Refactor payment service into smaller modules`
- `Document architecture decision for cache layer`

---

## 10. Erwartung an Mitwirkende

Mitwirkende sollen im Zweifel lieber:

- sauber fragen statt raten,
- klein und präzise ändern statt großflächig umbauen,
- dokumentieren statt implizit lassen,
- prüfen statt annehmen.
