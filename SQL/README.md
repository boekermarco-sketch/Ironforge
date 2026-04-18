# Ordner `SQL/` — Stand und Nutzung

Stand Doku: 2026-04-18 MEZ (Durchgang + gym80-Fix).

## Was wir mit lokalen SQL + passenden Bildern machen

| Ort | Rolle |
|-----|--------|
| **`static/img/catalog/`** (eGym, Matrix) und **`static/assets/gym80/`** (gym80) | **Kanonisch** für die laufende App und für Pfade wie `/static/...` bzw. `assets/gym80/...` in Dumps. Diese Dateien gehören ins Git (sind schon im Projekt). |
| **`SQL/**/*.sql` + dieses README** | **Archiv / Referenz**: SQLite-Dumps zum erneuten Import in eine lokale `.db`, Recherche, Diff. Werden versioniert. |
| **`SQL/gym80/*.webp`**, **`SQL/Matrix/images/*`**, **`SQL/egym_dump/*.jpeg`** | **Keine zweite Wahrheit im Repo**: identisch bzw. redundant zu `static/` (gym80) oder Arbeitskopie. Per **`.gitignore`** von Git ausgeschlossen, damit das Repo nicht mit hunderten Duplikat-Binärdateien wächst. **Lokal** kannst du sie behalten oder löschen — die App nutzt sie nicht direkt aus `SQL/`. |

Wenn du die `SQL/`-Bilder **doch** sichern willst: externes Backup, ZIP außerhalb des Repos, oder Git LFS (nur wenn du das bewusst einrichtest).

## Kurzfassung

- **Keine Bilder als Blob/BYTEA** in den `.sql`-Dateien: `image_url` bzw. `img` sind immer **Text** (HTTPS-URLs oder Pfade wie `assets/gym80/….webp`).
- Die **Binärdateien** (`.jpg`, `.jpeg`, `.webp`) liegen **parallel** in Unterordnern (`Matrix/images/`, `gym80/`, `egym_dump/`) — sie sind **nicht** in SQL eingebettet.
- **Supabase online** nutzt die Tabelle **`ifl_device_catalog`** (PostgreSQL). Diese wird im Projekt über **`setup_catalog.py`**, **`upload_catalog_images.py`** und ggf. **`populate_supabase_catalog.py`** / **`app.services.supabase_catalog_sync`** befüllt — **nicht** durch blindes Ausführen der SQLite-Dumps hier.

Eine einzige riesige „DELETE alles + INSERT“-SQL für Supabase wäre **riskant** (falsche Spalten, fehlende Storage-URLs, kein Rollback). Stattdessen: Katalog wie bisher per Scripts + Storage pflegen; nur gezielte Migrationen unter `docs/supabase_migrations/` im SQL Editor ausführen.

## Dateien

| Datei | Zweck | Bilder |
|--------|--------|--------|
| `egym_dump/egym_deutsch_final_download.sql` | SQLite: Tabellen `egym_*`, Geräteliste | Spalte `image_url`: meist **eGym-Marketing-URLs**, nicht die lokalen `.jpeg` aus `egym_dump/` |
| `egym_dump/*.jpeg` | Asset-Snapshots neben dem Dump | Für manuelle Zuordnung / statische Seiten |
| `Matrix/matrix_strength_final_complete.sql` | SQLite: `matrix_strength_devices` | Externe Bild-URLs in `image_url` |
| `Matrix/matrix_cardio_final_complete.sql` | SQLite: `matrix_cardio_devices` | Katalog-/Serien-URLs |
| `Matrix/images/*.jpg` | Rohbilder Matrix | Passend zu älteren Importpfaden |
| `gym80/gym80_devices_final.sql` | SQLite: `gym80_devices` | `assets/gym80/*.webp` oder gym80.de-URLs |
| `gym80/*.webp` | gym80-Vorschau-Bilder | Zu den `assets/gym80/`-Pfaden im SQL |

## Korrektur 2026-04-18

In `gym80/gym80_devices_final.sql` waren ab Zeile 16 die **Kategoriewerte** durch fehlerhaftes Escaping zerstört (`('(''(''''plate_loaded''''''` …). Das wurde auf `('plate_loaded',` bzw. `('weight_stack',` bereinigt, damit der Dump wieder importierbar ist.

## Wenn du Supabase „sauber“ neu aufsetzen willst

1. Backup / Export der aktuellen `ifl_device_catalog` (Dashboard oder `pg_dump`).
2. Lokal: `setup_catalog.py` / Sync-Skripte mit gültigen Keys ausführen, **Storage-URLs** in `img` setzen (`upload_catalog_images.py`).
3. Kein Ersatz durch rohes Zusammenkleben der SQLite-SQL-Dateien ohne Spalten-Mapping und ohne gültige **öffentliche** `img`-URLs.
