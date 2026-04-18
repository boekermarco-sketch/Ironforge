# Projektstand, Ideen und Beratungsprotokoll

**Zweck:** Zentrale Datei für aktuellen Stand, offene Punkte und beschlossene/ vorgeschlagene Ideen — bei größeren Änderungen am Projekt **kurz nachtragen**, damit nichts verloren geht.

**Letzte inhaltliche Pflege:** 2026-04-18 (Apple-Sync-Status + Katalog `target_key` / Audit / Pool-Favoriten)

---

## Kurz: Projekt im Blick

| Bereich | Technik / Ort |
|--------|----------------|
| Desktop-Dashboard | FastAPI + Jinja + SQLite `fitness.db`, lokal `start.bat` → Port 8080 |
| Training mobil | `training-preview.html`, GitHub Pages + Supabase (Sync, Katalog) |
| Gesundheitsdaten | Garmin/Withings/FatSecret/API; **Apple Health** zusätzlich per **iOS Shortcut → Supabase** `apple_health_daily`; optional **POST `/import/apple-health`** → SQLite |
| Gerätekatalog | SQLite-Tabellen `gym80_devices`, `matrix_*`, `egym_devices`; API `/import/catalog/search`; Sync `ifl_device_catalog` in Supabase |
| Doku-Pflicht | Diese Datei + bei Bedarf `CLAUDE.md` / `VORHABEN.md` ergänzen |

---

## 1. Apple Health / Auto-Export — Stand 2026-04-18 (lokal geprüft)

### Was wir hier sehen können (ohne Supabase-Zugang)

- **`fitness.db` zuletzt geändert:** 2026-04-17 ca. 13:37 (lokaler Datenträger).
- **`daily_logs`:** jüngstes Datum in der Abfrage **2026-04-14** (Quellen u. a. `myfitnesspal`, `gemischt`) — **keine** Einträge für 2026-04-15 bis 2026-04-18 in dieser Stichprobe.
- **`source`-Werte in SQLite:** `garmin`, `gemischt`, `manuell`, `myfitnesspal`, `withings` — kein dediziertes `apple_health`, falls Apple-Daten nur über Shortcut nach **Supabase** gehen und **lokal** kein `/import/apple-health` mehr gelaufen ist.

### Was das für „gestern 23 Uhr Export“ bedeutet

- Der **Ironforge Health Sync** (siehe `shortcut-anleitung.html`) ist so dokumentiert, dass die **Automatisierung um 23:30 Uhr** läuft — nicht zwingend 23:00.
- **Ob der Lauf gestern erfolgreich war**, sieht man zuverlässig:
  1. **iOS:** Kurzbefehle-App → Shortcut → **Letzte Ausführung** / Protokoll.
  2. **Supabase:** Table Editor → `apple_health_daily` → **neueste `date`-Zeile** und Zeitstempel (falls Spalte vorhanden).
  3. **Lokal:** nur wenn der Shortcut oder ein anderer Weg **`POST /import/apple-health`** triggert — dann steigen die Tage in `daily_logs` weiter an bzw. ändern sich Felder.

**Umgesetzt (Stand 2026-04-18)**

- Doku: **`docs/APPLE_HEALTH_SYNC.md`** (Shortcut „Letzte Ausführung“, Supabase-SQL, lokaler Pfad).
- **Supabase** `apple_health_daily`: neueste Zeile primär nach **`synced_at`**, sekundär nach Datum (`app/services/supabase_health.py`).
- **Lokal:** Tabelle **`app_kv_store`**, Key `apple_health_last_local` — gesetzt bei jedem erfolgreichen **`POST /import/apple-health`**; Anzeige auf dem **Dashboard** („Apple Health · Sync-Status“).

**Optional manuell**

- Shortcut-Laufzeit und letzte Supabase-Zeile hier in §1 als Stichdatum eintragen, wenn du festhalten willst, *dass* du an Tag X geprüft hast.

---

## 2. Gerätekatalog (gym80, Matrix, eGym) — bereinigen & Muskelgruppen

### Problem (vereinbart)

- Mobile Bedienung leidet unter **Filterkomplexität** und **inkonsistenten Ziel-Muskel-Filtern**.
- **Heuristiken** waren früher doppelt gepflegt; jetzt **ein Pfad**: `app/services/catalog_targets.py` (`infer_target`, `infer_stype`, `target_to_key`) + Overrides `device_target_overrides` für API-Suche, Supabase-Sync und `populate_supabase_catalog.py`.
- **Duplikate** (z. B. mehrere „Abduktor“): oft unterschiedliche `(category, serie, model)` nach SQL-Import oder unterschiedliche Dedupe-Keys (lokal `brand|name`, Supabase-Push `brand|name|target`).

### Empfohlenes Vorgehen (Phasen, ohne sofort alles zu bauen)

1. **Audit (read-only)**  
   - Pro Tabelle: `SELECT model, serie/series, category, muscle_groups, COUNT(*) … GROUP BY … HAVING COUNT(*)>1` und Stichproben „Abduktor“, „Multi-Station“.  
   - Export der **Ist-Liste** (CSV) für manuelle Review-Liste „Studio XY“.

2. **„Wahrheit“ definieren**  
   - Entscheidung: **Kanonische Felder** z. B. `target_key` (enum: Brust, Rücken, …), `session_type` (push/pull/legs/cardio/free), optional `movement_family`.  
   - Regel: **UI filtert nur noch auf diese Felder**, nicht auf live rekonstruierte Heuristik.

3. **Bereinigung**  
   - **Kuratierte Quelle** priorisieren (`setup_catalog.py`-Listen für Matrix/eGym sind bereits normativ).  
   - SQL-Dumps: nach Import **Merge/Dedupe-Regeln verschärfen** (z. B. normalisierter Modellname, Slug, oder manuelle Mapping-Tabelle „Rohname → Kanon“).

4. **Ein Inferenzpfad**  
   - Heuristik **einmal** (oder ganz weg), gleiche Logik für **SQLite-API und Supabase-Push**.

5. **Studio-UX** (größter Spaß-Faktor)  
   - Zusätzlich zum Weltkatalog: **„Mein Studio“** (20–40 Geräte), **Favoriten**, **zuletzt genutzt** — Suche dann trivial.

**Checkboxen (Stand 2026-04-18)**

- [x] Audit-Skript: `python -m app.services.catalog_audit` (Dubletten + Zielgruppen-Konflikte je SQLite)
- [x] Schema: Supabase-Spalten **`target_key`**, **`session_type`** (Migration `docs/supabase_migrations/ifl_device_catalog_target_key.sql`; `setup_catalog.py` CREATE erweitert)
- [ ] gym80 / matrix / egym Rohdaten manuell bereinigen + **erneut pushen** (nach Migration, falls Tabelle schon existierte)
- [x] `infer_target` einheitlich (`catalog_targets` + `resolve_catalog_row_targets`)
- [x] Mobile Pool: **Favoriten** (`ifl_pool_favorites_v1`) + Filter **„Nur Favoriten“**; Studio-Liste unverändert (`ifl_studio_equipment`)

---

## 3. Verschlüsselte Login-Seite — macht das Sinn?

### Kurzantwort

**Ja, eine Zugangssperre (Login) macht Sinn**, sobald die App **über das Internet** erreichbar ist (Render o. Ä.). **„Verschlüsselt“** im Sinne von HTTPS ist Standard — **„verschlüsselte Login-Seite“** allein ersetzt **kein** sauberes Auth-Konzept.

### Empfehlung (stufenweise)

| Stufe | Maßnahme | Nutzen |
|-------|-----------|--------|
| A | Nur lokal (`127.0.0.1`) + keine Port-Freigabe | Für rein privaten Desktop-Gebrauch oft ausreichend |
| B | HTTPS + **HTTP Basic Auth** oder **ein einfacher Passwort-Schutz** vor FastAPI | Schnell, besser als nichts; schwächer bei geteilten Passwörtern |
| C | **Echtes Login** (z. B. FastAPI-Users, OAuth, oder Reverse-Proxy mit Authelia) + Sessions | Seriös für persönliche Gesundheitsdaten |
| D | **Tailscale** / VPN: App gar nicht öffentlich | Sehr gut für „nur ich und meine Geräte“ |

**Verschlüsselung der Datenbank** (at rest) ist **zusätzlich** sinnvoll für sensible Notizen oder Backups — **ersetzt** aber nicht **Zugangskontrolle** zur laufenden Website.

**Ideen**

- [ ] Hosting-Entscheidung festhalten: öffentlich vs. nur VPN.
- [ ] Wenn Render: Mindestens Stufe B oder C dokumentieren und umsetzen.

---

## 4. Ideensammlung (kurz, nicht vergessen)

- **Garmin:** Login/429 — nur von vertrauenswürdiger IP, Token `.garth`, nicht von Render aus stressen; Fallback Export/CSV.
- **Doku-Pflege:** Jede größere Session: **1–3 Bulletpoints** unter „Letzte inhaltliche Pflege“ + Datum.
- **VORHABEN.md:** ist älter (16.04.2026); bei großen Meilensteinen entweder aktualisieren oder auf diese Datei verweisen.

---

## 5. Changelog (manuell / Agent kurz eintragen)

| Datum | Was |
|-------|-----|
| 2026-04-18 | Datei angelegt: Stand Health lokal (`daily_logs` bis 14.04.), Katalog-Vorgehen, Login-Beratung, Projektüberblick. Temporäres Prüfskript entfernt. |
| 2026-04-18 | **Mobile vereinfacht** (`training-preview.html`, Build 2026-04-18 14:15): nur noch **Training** + **Rechner** (Bottom-Nav); Heute/Übungen/Fortschritt-Charts von Mobile entfernt → **Desktop**. Training: **Schnellsuche**-Sheet (Volltext Pool + aktive Session) + **Pool**-Button. Rechner-Screen: Studio, KFA/Gewicht, **1RM-Tabelle je Gruppe/Studio**, Epley **Zielgewicht** + **1RM aus Satz**, Studio-Geräteliste. `weightFrom1RM()` ergänzt. |
| 2026-04-18 | **Apple + Katalog:** `app_kv_store` / `apple_health_last_local`; Dashboard „Apple Health · Sync-Status“; Supabase-Zeilen nach `synced_at`; Doku `docs/APPLE_HEALTH_SYNC.md`. Katalog: `target_key` + `session_type` im Sync, Migration-SQL, `python -m app.services.catalog_audit`, API `/import/catalog/search` liefert `targetKey`/`sessionType`. `populate_supabase_catalog.py` nutzt `read_sqlite_device_catalog_rows`. Training-Pool: Favoriten + Filter (Build 21:40). |
| 2026-04-18 | **Umsetzung Freigabe 1–3** (`training-preview.html`, Build-Stamp 2026-04-18 10:30): PWA/Meta-Tags; Mobile `body.ifl-mobile-app` blendet Desktop-Main aus; Session-Overlay nur `m-ex-scroll` scrollt; Rand-Wischen wechselt Heute/Training/Übungen/Fortschritt; Subtab-Leiste wischt Push…Cardio; Tab „Fortschritt“ mit KPI + 28-Tage-Balkendiagramm + Top-Übungen; Heute: horizontale Snap-Karten (7d Sessions/Volumen); **Studio-Geräte** pro Studio (Textarea) → `localStorage` `ifl_studio_equipment` + Cloud `buildAppState` / strukturiert `studio_equipment` Meta + Vault-Blob; Pool-Sheet: Checkbox „Nur Studio-Liste“; Fixes: `mHeaderBack` → Heute, `openLoggerForExercise` übergibt Objekt, Letzter-Log `type`/`w`/`r`, Pool „Alle“, Session-Today `id`/`exId`. |
