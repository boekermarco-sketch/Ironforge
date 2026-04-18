# Apple Health · Shortcut · Supabase · lokaler Import

## Wo du den Erfolg prüfst

### 1. iOS-Kurzbefehl (letzte Ausführung)

- App **Kurzbefehle** öffnen → deinen Shortcut **Ironforge Health Sync** (o. Ä.) wählen.
- Unten **⋯** (Details) → Bereich **„Letzte Ausführung“** / Automatisierungs-Historie (je nach iOS-Version).
- So siehst du, **wann** der Shortcut zuletzt gelaufen ist und ob er mit Fehler endete.

### 2. Supabase (`apple_health_daily`)

- Table Editor → `apple_health_daily`.
- Sortierung nach **`synced_at`** absteigend (oder nach `date`): oberste Zeile = zuletzt eingespielt.
- SQL-Kurzcheck:

```sql
SELECT date, synced_at, calories, protein_g, steps
FROM apple_health_daily
ORDER BY synced_at DESC NULLS LAST, date DESC
LIMIT 5;
```

### 3. Lokales Dashboard (FastAPI)

Nach erfolgreichem **`POST /import/apple-health`** schreibt die App einen Eintrag in **`app_kv_store`** (`apple_health_last_local`):

- **received_at**: Zeitpunkt des Imports (UTC, ISO).
- **entry_date**: betroffenes Tagesdatum.
- **fields**: welche Felder gesetzt wurden.

Auf dem **Dashboard** erscheint dazu ein kurzer Statusblock („Letzter lokaler Apple-Import“) neben den Supabase-Daten.

## Kurzüberblick Datenflüsse

| Weg | Ziel |
|-----|------|
| Shortcut → Supabase REST | Tabelle `apple_health_daily` (Dashboard liest per Anon-Key). |
| Shortcut / anderer Client → `POST /import/apple-health` | SQLite `daily_logs` + Metadaten `apple_health_last_local`. |

Beides parallel nutzen ist möglich; das Dashboard kombiniert Gewicht/KFA/Ruhepuls aus Supabase, wenn lokal etwas fehlt.

---

## 4. Prüfprotokoll (manuell, MEZ)

Hier kannst du Stichprotokolle festhalten (Zeit immer als **MEZ** notieren).

| Geprüft am (MEZ) | Shortcut: letzte Ausführung (Datum/Uhrzeit) | Supabase: neueste Zeile `date` / `synced_at` | Lokaler POST / Dashboard ok? |
|-------------------|---------------------------------------------|-----------------------------------------------|--------------------------------|
| 2026-04-18 14:27  | *bitte eintragen*                           | *bitte eintragen*                             | *ja/nein*                      |

**Hinweis:** Nach Änderungen an `training-preview.html` oder am FastAPI-Dashboard steht im UI bzw. im HTML-Kommentar ein **Build-/Änderungsstempel (MEZ)**.
