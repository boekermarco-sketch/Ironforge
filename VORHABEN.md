# Vorhaben & Roadmap — Ironforge Fitness System
Stand: 16.04.2026

---

## 1. Gerätekatalog (Matrix + eGym)

### ✅ Erledigt
- Bilder aus matrix_geraete_mit_bildern.xlsx extrahiert → `static/img/catalog/matrix/`
- eGym-Bilder kopiert → `static/img/catalog/egym/`
- SQLite-Tabellen befüllt: `matrix_strength_devices`, `matrix_cardio_devices`, `egym_devices`
- Supabase `ifl_device_catalog` befüllt (via anon key)
- Deutsche Namen für alle Geräte vergeben

### ✅ Erledigt
- Supabase Storage Bucket `device-images` erstellt (public)
- 54/54 Bilder hochgeladen → `device-images/matrix/` + `device-images/egym/`
- SQLite + Supabase `ifl_device_catalog` mit echten Storage-URLs aktualisiert
- Katalog mit Bildern funktioniert auf iPhone (GitHub Pages)

### 🔲 Noch offen
- **Multi-Station Feinschliff**: 10x "Multi-Station 1-10" → Umbenennung wenn klar welche Geräte
- **gym80-Katalog**: Bilder fehlen noch → gleiches Verfahren wenn Bilder vorliegen

---

## 2. Apple Health → Supabase (täglicher Sync)

### ✅ Erledigt
- Tabelle `apple_health_daily` SQL liegt in `shortcut-anleitung.html` (einmalig in Supabase ausführen)
- iOS Shortcut Anleitung: `shortcut-anleitung.html` im Projektordner
- MFP Apple Health Sync aktiviert (seit 15.04.2026)
- **FastAPI-Endpunkt** `POST /import/apple-health` implementiert → UPSERT in SQLite `daily_logs`

### 🔲 Noch offen
- **Supabase: Tabelle anlegen** (SQL aus shortcut-anleitung.html in Supabase SQL Editor ausführen)
- **iOS Shortcut bauen** (Anleitung in shortcut-anleitung.html)
- **Backfill historischer Daten**: Apple Health Export liegt in `C:\Users\boeke\Downloads\Apple Health\Export\` → einmaliger Import per Script möglich

---

## 3. Training-App Mobile (training-preview.html)

### ✅ Erledigt
- GitHub Pages läuft (/Ironforge/)
- Supabase Sync (Upload/Download)
- Mobile Session-Flow (Bottom-Tabbar, Sortiermodus, Pool-Add)
- Gerätekatalog mit DB-Backend + Supabase Fallback
- **Mobile UX-Feinschliff** implementiert:
  - 3 Haupttabs im Bottom-Nav: Stats / Training / History
  - Rest-Timer: `position:fixed` floating über Bottom-Nav
  - Logger-Modal: fullscreen auf Mobile
  - iOS-Feel Transitions (`cubic-bezier(0.4,0,0.2,1)`)
  - `overflow:hidden` body auf Mobile, inneres Scroll
- **Session-Fokus-Flow** finalisiert (Focus-Bar + Modal-Vollbild)

### 🔲 Noch offen
- Sortiermodus iOS-Touch-Haptik/Visuelles Verhalten (Feinschliff)
- Structured Sync braucht finale Supabase DB-Tabellen + Policies

---

## 4. Dashboard & Tageslog (FastAPI lokal)

### 🔲 Noch offen
- Garmin-Fallback: HRV, Body Battery, Sleep Score, Ruhepuls (90-Tage-Lookback)
- Recovery-Card: Training Status + Atemfrequenz
- Chart Multi-Metrik: Gewicht / KFA / Muskelmasse dual Y-Achse
- KFA%-Ziel: Fortschrittsanzeige
- **Apple Health Import**: Daten aus Supabase `apple_health_daily` ins Dashboard einbauen (MFP-Makros als Tageslog-Ersatz/Ergänzung)

---

## 5. Deployment (zukünftig)

### Entscheidung
- **iPhone / unterwegs**: GitHub Pages + Supabase (bereits aktiv)
- **Desktop lokal**: start.bat + SQLite (bleibt)
- **Server**: Oracle Cloud Free Tier oder Render/Railway (wenn FastAPI online gebraucht wird)

### 🔲 Wenn Server gebraucht wird
- FastAPI auf Server deployen
- Nginx Reverse Proxy (kein :8080)
- GitHub-Repo für Code + git pull für Updates
- `.env` auf Server sichern

---

## 6. Offene Kleinigkeiten

- Check-in Verlauf prüfen
- Ereignisse Stack-Timeline (DoseEvent-Daten)

---

## Reihenfolge nächste Sessions

1. ✅ Gerätekatalog einbauen (Matrix + eGym)
2. ✅ Supabase Storage Bucket + Bild-Upload (54 Bilder live)
3. Supabase Tabelle `apple_health_daily` anlegen + iOS Shortcut bauen
4. Mobile UX-Feinschliff (aus Mobile seite.docx)
5. Dashboard Apple-Health-Integration
6. Kleinigkeiten: FatSecret, Check-in, Stack-Timeline
