# CLAUDE.md – Projektregeln für Claude (AI-Coding-Assistent)

Dieses Dokument definiert die **universellen Regeln und Prinzipien**, nach denen Claude in diesem Projekt arbeitet – unabhängig davon, ob es sich um ein bestehendes Projekt, ein neues Modul oder eine komplette Neuimplementierung handelt.

---

## 1. Rolle und Arbeitsweise

Du arbeitest als **Gremium aus Senior Software Engineers**:

- Software Architect
- Senior Backend Engineer
- Senior Frontend Engineer
- Senior Security Engineer
- Senior Performance Engineer
- Senior QA/Test Engineer
- Senior Maintainability / Clean-Code Reviewer
- Technical Writer / Documentation Engineer

Du handelst **nicht vorschnell**. Du untersuchst zuerst den vorhandenen Stand, entscheidest dann den korrekten Modus und arbeitest danach strikt strukturiert.

---

## 2. Arbeitsmodus-Erkennung

Bevor du quelque Code änderst oder schreibst, bestimme zuerst den Modus:

1. **Review** – Code existiert, soll nur geprüft werden  
2. **Refactor** – Code existiert, soll strukturell verbessert werden  
3. **Erweiterung** – Neues Feature/Modul zum bestehenden Code  
4. **Neuimplementierung** – Neues Modul / Neues Projekt

Erst danach beginnst du mit Plan und Umsetzung.

---

## 3. Arbeitsphasen (strikte Reihenfolge)

### PHASE 1 – Analyse

- Lies zuerst relevante Dateien, Ordner, Schnittstellen, Konfigurationen und Tests.
- Verstehe bestehende Architektur, Namenskonventionen, Muster, Abhängigkeiten.
- Spekuliere nicht über nicht geprüfte Dateien oder Verhalten.
- Wenn Informationen fehlen, benenne die Lücken klar.

### PHASE 2 – Expertenbewertung

Bewerte das Vorhaben aus Sicht des Senior-Engineer-Gremiums:

- Architektur
- Modularität
- Lesbarkeit
- Wartbarkeit
- Erweiterbarkeit
- Sicherheit
- Performance
- Fehlerbehandlung
- Testbarkeit
- Konsistenz mit bestehendem Projekt
- Dokumentation

### PHASE 3 – Plan

Erstelle vor jeder Änderung einen konkreten Plan:

- Was bleibt unverändert?
- Was muss geändert werden?
- Welche Module/Funktionen/Dateien sind betroffen?
- Welche Risiken bestehen?
- Welche Tests oder Checks sind nötig?

### PHASE 4 – Umsetzung oder Review

**Wenn Code neu geschrieben oder geändert werden soll:**

- Implementiere sauber, modern, modular.
- Nutze kleine, klar abgegrenzte Funktionen/Module.
- Vermeide Duplikate, enge Kopplung, unnötige Komplexität.
- Respektiere bestehende Projektmuster, sofern sie nicht klar problematisch sind.
- Mache keine unnötigen Refactors außerhalb des Scopes.

**Wenn Code nur geprüft werden soll:**

- Führe ein strenges Review durch.
- Trenne Pflichtprobleme von optionalen Verbesserungen.
- Priorisiere nach Schweregrad:
  - **Kritisch** (Funktionalität, Sicherheit, Datenkorruption)
  - **Wichtig** (Wartbarkeit, Fehlerbehandlung, Performance)
  - **Optional** (Stil, kleine Verbesserungen)

### PHASE 5 – Selbst-Check

Nach jeder Implementierung oder Überarbeitung führe einen strengen Self-Review durch:

- fachliche Korrektheit
- Logikfehler
- Seiteneffekte
- unnötige Komplexität
- schlechte Benennungen
- zu große Funktionen/Klassen
- fehlende Trennung von Verantwortlichkeiten
- doppelte Logik
- schwache Fehlerbehandlung
- fehlende Validierung
- Sicherheitsrisiken
- Performance-Probleme
- Edge Cases
- fehlende/ungenügende Tests
- fehlende/veraltete Dokumentation

Wenn du Mängel findest:
1. Liste sie kurz auf.
2. Behebe sie direkt.
3. Zeige danach die überarbeitete finale Version.

### PHASE 6 – Dokumentation

Dokumentiere das Ergebnis immer mit:

- Kurzbeschreibung des Problems / Ziels
- gewählter Modus (Review / Refactor / Erweiterung / Neuimplementierung)
- Architektur- bzw. Modulentscheidung
- geänderte Dateien / betroffene Bereiche
- wichtigste Designentscheidungen
- Risiken / offene Punkte
- Teststrategie
- kurze Wartungshinweise

---

## 4. Qualitätskriterien

Der Code muss immer:

- Clean Code erfüllen
- moderne und modulare Struktur haben
- klare Verantwortlichkeiten aufweisen
- geringe Kopplung und hohe Kohäsion besitzen
- sprechende Namen verwenden
- robuste Fehlerbehandlung haben
- sichere Standardentscheidungen treffen
- nachvollziehbare Architektur aufweisen
- gut erweiterbar und testbar sein
- sauber dokumentiert sein

---

## 5. Verhaltensregeln

- Erst analysieren, dann planen, dann umsetzen.
- Keine Annahmen ohne Prüfung.
- Keine unnötige Komplexität.
- Keine unnötigen Kommentare im Code.
- Kommentare nur dort, wo Absicht oder Kontext sonst unklar wäre.
- Dokumentation so schreiben, dass ein anderer Entwickler die Entscheidung später versteht.
- Bestehenden Code nicht unnötig komplett umbauen, wenn gezielte Verbesserung besser ist.
- Bei unklaren Anforderungen erst präzise Rückfragen stellen.

---

## 6. Ausgabeformat

Jede signifikante Arbeit soll in dieser Struktur ausgegeben werden:

A. Modus-Erkennung  
B. Analyse des Ist-Zustands  
C. Bewertung durch das Senior-Engineer-Gremium  
D. Umsetzungs- oder Review-Plan  
E. Code oder Review-Findings  
F. Self-Check  
G. Dokumentation / Änderungsprotokoll  
H. Finale Version bzw. finale Empfehlung

---

## 7. Zusatzregeln

- Nenne bei jedem relevanten Problem möglichst Datei, Modul, Funktion und Auswirkung.
- Unterscheide strikt zwischen **Muss-Korrekturen** und **Kann-Verbesserungen**.
- Verändere keine unbeteiligten Bereiche ohne klaren Grund.
- Ergänze oder aktualisiere Dokumentation, README, Architekturhinweise oder In-Code-Doku, wenn sich Verhalten, Struktur oder Nutzung geändert haben.
- Wenn Tests fehlen, schlage konkrete Tests vor oder implementiere sie.
- Dokumentiere wichtige Architekturentscheidungen und verworfene Alternativen kurz, aber nachvollziehbar.

---

## 8. Projektstand & Implementierungshistorie

### Stand: 13.04.2026

#### Architektur
- **Backend:** FastAPI + SQLAlchemy ORM + SQLite (`fitness.db`), Port 8080
- **Frontend:** Jinja2-Templates, Chart.js 4.4.0, kein JS-Framework
- **Start:** `start.bat` (lädt `.env`, startet uvicorn)
- **Fonts:** Bebas Neue (Display), Barlow (Text), JetBrains Mono (Zahlen/Code)
- **CSS:** `static/css/style.css?v=6` – Design-System mit Custom Properties, Hintergrund `#080808`, Akzent Orange `#f97316`

#### Implementierte Module & Routen

| Modul | Router | Template | Beschreibung |
|-------|--------|----------|--------------|
| Dashboard | `app/routers/dashboard.py` | `templates/dashboard.html` | Hero-Gewicht, Stat-Grid, Charts |
| Stack | `app/routers/stack.py` | `templates/stack.html` | Bento-Grid nach Zeitslots, Inline-Edit, DOCX-Download |
| Blutbilder | `app/routers/blood.py` | `templates/blood_panel.html` | Blutbild-Übersicht, PDF-Upload |
| Check-in | `app/routers/checkin.py` | `templates/checkin.html` | Fotogalerie, Analysen, Fortlaufender Verlauf |
| Tageslog | `app/routers/daily_log.py` | `templates/daily_log.html` | Tägliche Einträge, Garmin/Withings/FatSecret |
| Import | `app/routers/imports.py` | `templates/imports.html` | Garmin + Withings + FatSecret API + CSV |

#### Datenquellen & API-Integrationen (Stand 13.04.2026)

| Quelle | Status | Auth | Notizen |
|--------|--------|------|---------|
| Garmin | ✅ aktiv | GARMIN_EMAIL + GARMIN_PASSWORD in `.env` | 24h-Sperre nach Abruf (Rate-Limit-Schutz, localStorage) |
| Withings | ✅ aktiv | `.withings_credentials.json` (OAuth 2.0) | Backfill 90 Tage verfügbar |
| FatSecret | ✅ aktiv | Consumer Key + Secret in `.env` | 2-legged OAuth 1.0, `signature_type=body`, funktioniert |
| Blutbilder | ✅ aktiv | – | PDF-Parser (`pdfplumber`), Ordner `data/Blutbilder/` + `Imports/Blutbilder/` |

#### Training-Preview (standalone)
- **Datei:** `training-preview.html` – Single-File-App, localStorage, kein Server
- **DB_VERSION:** 6 (bei Änderung inkrementieren → Reset der DB)
- **Übungen:** IDs 1–28, Pool nach Kategorie (push/pull/legs/core/free)
- **Tabs:** push, pull_a, pull_b, legs, free + pool-Übersicht
- **Features:** Session-Logger Modal, Session bearbeiten/löschen Modal, Template laden, Kalender-Ansicht
- **Deployment-Plan:** GitHub Pages für mobilen Studio-Einsatz, später Supabase für Sync

#### FatSecret-Details (wichtig für zukünftige Sessions)
- **Auth:** 2-legged OAuth 1.0 – NUR Consumer Key + Secret aus `.env`, kein User-Token nötig
- **Kritisch:** `signature_type="body"` in `OAuth1()`-Konstruktor – ohne das "Invalid signature"
- **3-legged OAuth 1.0** (www.fatsecret.com) ist Cloudflare-geblockt für Python-Scripts → nicht nutzen
- **Service:** `app/services/fatsecret_fetch.py`, Endpunkt `platform.fatsecret.com/rest/server.api`
- **CSV-Fallback:** `app/services/fatsecret_csv.py`, Ordner `Imports/FatSecret/`

#### Check-in / Foto-Analyse-Workflow
- **Kein Anthropic API Key** → manueller Workflow:
  1. User legt Foto in `Imports/CheckIn_Fotos/<datum>/` ab
  2. User teilt Foto im Chat mit Claude
  3. Claude analysiert und schreibt Analyse direkt in DB (`JournalEntry.analysis_text`)
- Vorhandene Analysen: 29.03.2026 (Woche 5), 03.04.2026 (Woche 6/Tag 40)

#### Stack-Modul Details
- Zeitslots: `07:00 – Nüchtern`, `10–11 Uhr`, `17–18 Uhr`, `21–22 Uhr`, `Injektionen`, `Sonstige`
- Inline-Edit via `toggleEdit(id)` – verschachtelte `<form>`-Tags umgangen mit Hidden-Form + JS
- DOCX-Download: `/stack/download` – python-docx, gruppiert nach Zeitslots

#### Bekannte Besonderheiten & Fallstricke
- **Browser-Cache:** CSS-Änderungen → Ctrl+Shift+R + `?v=N` inkrementieren
- **Jinja2 Datumsrechnung:** `blast_start` immer aus Router übergeben, nicht im Template berechnen
- **`.env` laden in start.bat:** `for /f "usebackq tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"`
- **training-preview.html DB-Reset:** DB_VERSION erhöhen wenn Übungsstruktur sich ändert
- **Pflicht bei `training-preview.html`-Änderungen:** `BUILD_STAMP` immer auf aktuelle lokale Zeit (`YYYY-MM-DD HH:MM`) setzen, damit oben rechts die echte Build-Version sichtbar ist.

---

## 9. TODO-Liste (Stand 13.04.2026)

### ✅ Erledigt

- [x] Garmin API-Import (live fetch, 24h-Lock)
- [x] Withings API-Import (live fetch + Backfill 90 Tage)
- [x] FatSecret API-Import (2-legged OAuth 1.0, funktioniert)
- [x] FatSecret CSV-Import (Fallback, `Imports/FatSecret/`)
- [x] Blutbild-PDF-Parser
- [x] Import-Seite mit Status-Übersicht + allen Buttons
- [x] Training-Preview: Übungs-Pool (IDs 1–28), alle Pool-Übungen vorhanden
- [x] Training-Preview: Session-Logger Modal
- [x] Training-Preview: Session bearbeiten + löschen (Modal, persistent)
- [x] Training-Preview: Template laden (`loadTemplate()`)
- [x] Training-Preview: `changeTab()` für pull_a/pull_b korrekt
- [x] Training-Preview: Kalender-Ansicht

### 🔲 Offen – Dashboard & Tageslog

- [ ] **Dashboard Garmin-Fallback:** HRV, Body Battery, Sleep Score, Ruhepuls, TR, Training Status, Atemfrequenz — 90-Tage-Lookback wenn kein aktueller Fetch (`app/routers/dashboard.py`)
- [ ] **Dashboard Recovery-Card:** Training Status + Atemfrequenz ergänzen (`templates/dashboard.html`)
- [ ] **Dashboard Vitals-Card:** BP + PWV mit Fallback, Layout-Verbesserung
- [ ] **Dashboard Chart Multi-Metrik:** Gewicht / KFA / Muskelmasse dual Y-Achse, umschaltbar (`templates/dashboard.html` + `/tageslog/api/chart`)
- [ ] **Dashboard KFA%-Ziel:** Aktueller KFA% vs. Zielwert, Fortschrittsanzeige
- [ ] **Tageslog:** Training Status + Atemfrequenz prüfen/ergänzen
- [ ] **Dashboard IFTTT Bin-Import:** IFTTT-Events per Import/Start-Flow ins Dashboard übernehmen (inkl. Status/Fehleranzeige)

### 🔲 Offen – Training-Preview (training-preview.html)

- [ ] **Drag-to-Reorder:** Übungen innerhalb aktiver Session per Drag neu anordnen
- [ ] **Forge Analytics:** Multi-Compound Plotter + Peptid/Vial-Rechner als Overlay
  - CompoundDB: Testo E/C/P/D, Sustanon, Tren E/A, Masteron E/P, Primo, Deca, NPP, Bolde, GLP-1, HGH, BPC-157, TB-500
  - Code bereits vollständig ausgearbeitet (wartet auf Einbau)
- [ ] **GitHub Pages Deployment:** `training-preview.html` als `index.html` in GitHub-Repo → mobil im Studio nutzbar

### 🔲 Offen – Weitere Module

- [ ] **Ereignisse Stack-Timeline Stufe 1:** Chronologische Timeline aus vorhandenen DoseEvent-Daten
- [ ] **Stack-Changelog Stufe 2:** Neues `StackChangeLog`-Model, automatisches Logging bei jeder Änderung
- [ ] **Check-in Verlauf:** Status prüfen, ggf. Bugs beheben

### 🔲 Offen – Training-App V1 (Pflichtenheft Abschnitt 9)

Vollständige neue App-Architektur gemäß Pflichtenheft:
- [ ] Supabase-Projekt anlegen (Schema: profiles, studios, exercises, sessions, session_sets)
- [ ] Training-App auf GitHub Pages (statischer Client mit Supabase-Backend)
- [ ] Mobile Session-Flow (Long-Press Reorder, Floating Rest-Timer, Touch-first)
- [ ] Studio-spezifische Geräte-Pools + Globaler Pool
- [ ] Progress je Übung + je Bewegungsgruppe/Familie
- [ ] Relative Last / Studio-Korrelation (manuelle Faktoren Stufe 1)
- [ ] Verschlüsselung sensibler Stack-Notizen (AES-256, clientseitig)
- [ ] FatSecret-Import robust machen (Token-Handling, Duplikatschutz, Fehlerprotokoll)

### 🔲 Offen – Deployment Haupt-App (FastAPI)

- [ ] Oracle Cloud Free Tier VM einrichten (einmalig ~2-3h)
- [ ] GitHub-Repo für Projektcode anlegen
- [ ] Deploy-Workflow: git push → git pull auf Server → App-Neustart
- [ ] Nginx als Reverse Proxy (kein :8080 im URL)
- [ ] Optional: eigene Domain

---

## 10. Pflichtenheft V1 – Mobile Trainingstagebuch (13.04.2026)

---

## 9. Pflichtenheft V1 – Mobile Trainingstagebuch (13.04.2026)

### 9.1 Zielbild

Das System soll als alltagstaugliches Trainingstagebuch auf dem iPhone funktionieren und in verschiedenen Studios nutzbar sein. Prioritaet hat robuste Funktion vor Design-Ausbau.

Kernziele:
- Training mobil schnell loggen (inkl. Satz-Flow und Rest-Timer)
- Sessions spaeter bearbeiten und verlaesslich speichern
- Studio-uebergreifende Vergleichbarkeit (Maschinenunterschiede beruecksichtigen)
- Daten dauerhaft synchron zwischen Geraeten verfuegbar

### 9.2 Architekturentscheidung (V1)

Verbindliche Basis fuer V1:
- Frontend/Hosting: GitHub Pages (statischer App-Client)
- Datenbank/Auth/API: Supabase Free Tier
- Charts/Visualisierung: Chart.js
- Ernaehrungsanbindung: FatSecret API (spaeter stabilisieren)

Leitlinie:
- Offline-first UX mit lokalem Cache, aber zentrale Persistenz in Supabase.
- Keine sensiblen Secrets im Clientcode.

### 9.3 Muss-Anforderungen (V1)

#### A) Mobile Training-Flow
- Tabwechsel Push/Pull A/Pull B/Beine/Frei muss mobil klar sichtbare Zustandsaenderung liefern.
- Pro Session muss ein Standard-Template ladbar sein.
- Reihenfolge der aktiven Uebungen muss aenderbar sein.
- Uebungen muessen aus dem Pool in die aktive Session uebernehmbar sein (auch ohne Drag als explizite Plus-Aktion).
- Neue Uebungen muessen aus der Session heraus anlegbar sein.
- Session-Eintraege muessen nachtraeglich bearbeitbar bleiben.

#### B) Interaktion & iPhone-Pattern
- Long-Press auf Uebung aktiviert Reorder/Edit-Modus (iOS-aehnlicher "Wackelmodus").
- Rest-Timer muss nach Satzabschluss mobil sichtbar bleiben (sticky/floating), bis er endet oder gestoppt wird.
- App-Gefuehl auf Mobile (kompakter Session-Header, klare Hauptaktionen, Touch-first Controls).

#### C) Datenmodell & Pools
- Globaler Standard-Pool fuer alle Studios.
- Zusaetzlicher studio-spezifischer Pool je Studio.
- Uebungen erhalten stabile IDs, Kategorie, Bewegungsgruppe/Familie, Hersteller, Maschinentyp.

#### D) Progress & Analyse
- Progress pro Uebung (historisch je Studio).
- Progress pro Bewegungsgruppe/Familie (z. B. alle Schraegbank-Varianten zusammenfassen).
- Studiovergleich mit Korrelation (Relative Last) vorbereiten.

#### E) Datenhaltung/Sync
- Start mit Supabase direkt in V1 (nicht nur localStorage).
- Lokaler Fallback/Cache fuer schnelle mobile Nutzung.
- Backup/Restore-Mechanismus weiterhin verfuegbar.

### 9.4 Kann-Anforderungen (V1.x)

- Dashboard-Integration der Trainingsresultate (Sessions, Volumen, PRs, Progress).
- Injektions-/Steroid- und Peptid-Rechner als separates Dashboard-Modul.
- Erweiterte Planer-Ansicht fuer Session-Zuweisungen (Tag A/Tag B-Konfigurator).

### 9.5 Nicht in V1 (bewusst spaeter)

- Vollautomatischer KI-Lernmodus fuer Lastkorrektur ohne initiale Regelbasis.
- Vollstaendige Echtzeit-Sync bei instabilen Verbindungen ohne Konfliktstrategie.
- Umfangreiche Design-Politur vor Stabilisierung des Kernflows.

### 9.6 Studio-Korrelation (Relative Last) – Fachlogik

Formelbasis:
- Gewicht_Ziel = Gewicht_Basis * k

V1-Umsetzung (stufenweise):
1. Manuelle Faktoren je Maschinenpaar/Bewegungsgruppe (Quick-Fix).
2. 1RM-/Intensitaetsbasierte Umrechnung pro Studio und Uebungsfamilie.
3. Lernmodus als V2: User-Feedback (subjektive Schwere) passt Faktor langfristig an.

### 9.7 Sicherheit & Datenschutz

Trennmodell:
- Normale Trainingsdaten: unverschluesselt speicherbar fuer Auswertung.
- Sensible Stack-/Medikationsnotizen: clientseitig verschluesseln (AES-256).

Pflichtregeln:
- Schluesselableitung mit Salt und starkem Verfahren (z. B. PBKDF2/Argon2).
- Pro Datensatz IV/Nonce; keine statischen Keys.
- Supabase RLS strikt aktiv.
- Service-Keys niemals im Frontend.

### 9.8 Geraetekatalog (schrittweise Ladung)

Anforderung:
- Katalog nicht komplett vorladen.
- Abruf nur bei gesetzten Filtern (z. B. Hersteller gym80 + Zielmuskel Brust).
- Suchergebnis zeigt Geraete inkl. Bild.
- Bei Uebernahme in den Pool werden Metadaten/Bilder gespeichert.

### 9.9 FatSecret – Pflicht-Fixpaket

Der FatSecret-Import gilt als unzureichend stabil und wird als eigener Arbeitsblock geplant:
- OAuth-/Token-Handling robust machen (Ablauf, Refresh, Fehlerfaelle).
- Datenmapping auf Tageslog eindeutig und reproduzierbar.
- Duplikatschutz bei Re-Import.
- Monitoring/Fehlerprotokoll fuer fehlgeschlagene Abrufe.

### 9.10 Datenbankstart (Entscheidung)

Entscheidung: Ja, Datenbankstart sofort in V1.

Minimales Startschema:
- profiles
- studios
- exercises (global/studio-spezifisch)
- exercise_groups (Familien/Bewegungsgruppen)
- sessions
- session_sets
- optional spaeter: device_factors, import_jobs, encrypted_notes

Begruendung:
- Verhindert doppelte Migrationen von localStorage zu Backend.
- Macht Mehrgeraete-Nutzung und spaetere Dashboard-Integration direkt anschlussfaehig.

### 9.11 Akzeptanzkriterien (Definition of Done V1)

V1 gilt als funktional erreicht, wenn:
- Mobile Session-Flow auf iPhone ohne Workarounds nutzbar ist.
- Push/Pull-Tabs sichtbare und nachvollziehbare Wechsel zeigen.
- Reorder, Pool-Add und Session-Bearbeitung stabil funktionieren.
- Rest-Timer mobil durchgaengig sichtbar ist.
- Daten in Supabase gespeichert und zwischen zwei Geraeten nachvollziehbar synchron sind.
- Progress je Uebung und je Bewegungsgruppe abrufbar ist.

---

## 11. Statusabgleich & Roadmap-Update (14.04.2026)

### 11.1 Abgleich mit aktuellem Stand (Agent + Claude)

#### ✅ Bereits umgesetzt in `training-preview.html`
- GitHub Pages laeuft (`/Ironforge/`), Training-Preview ist online erreichbar.
- Supabase Sync-Setup (Erststart-Overlay) mit Profil, URL, anon key, Verbindungstest.
- Cloud-Sync Buttons: Upload/Download + Statusanzeige.
- Mobile Session-Flow deutlich verbessert:
  - Bottom-Tabbar (Push/Pull A/Pull B/Beine/Frei)
  - Sortiermodus (Long-Press + sichtbarer Modus)
  - `+ Session` aus Pool
  - Reorder-Fallback (`↑`/`↓`) zusaetzlich zu Drag
  - "Speichern & naechste Uebung"
- Session-Bearbeitung und Kalender bleiben intakt.
- Studio-Korrelation V1:
  - Basis-Studio + Ziel-Studio + Faktor `k`
  - Speichern je Bewegungsgruppe/Studio-Paar
- Progress-Tabellen:
  - pro Uebung
  - pro Bewegungsgruppe
- Pool-Scopes:
  - Standard-Pool (global)
  - Studio-Pool (pro Studio)
- Geraetekatalog V1:
  - Filter (Hersteller/Zielmuskel/Suche/Session-Typ)
  - stueckweises Laden
  - `+ Pool` und `+ Session` aus Katalog

#### 🟡 Teilweise umgesetzt / verfeinern
- Timer ist sticky sichtbar, aber noch nicht optimal "im Uebungs-Element" integriert.
- Sortiermodus vorhanden, iOS-Feinschliff (Touch-Haptik/Visuelles Verhalten) noch offen.
- Sync hat zwei Modi (`state_v1` / `structured_v1`), strukturierter Modus braucht finale DB-Tabellen + Policies.

#### 🔲 Noch offen (aus vorherigen TODOs + neuem Input)
- Dashboard-Integration der Trainingsdaten (Summary/Volumen/PR/Progress).
- FatSecret-Import final robust machen (Tokenfluss, Duplikatschutz, Fehlermeldungen).
- Security-Hardening fuer sensible Inhalte (AES-Flow + Schlüsselstrategie + saubere UX).
- Check-in/Stack Timeline offene Punkte.

### 11.2 Mobile Produktentscheidung (verbindlich)

Die App folgt jetzt einem 3-Phasen-Flow pro Trainingstag:
1. **Check-In**: Gym/Studio waehlen (einmal).
2. **Planung/Pool**: Session zusammenstellen + tauschen.
3. **Session**: Fokus auf Set-Logging, Timer, naechste Uebung.

### 11.3 UI/UX Leitplanken Mobile

- Optionale Mobile-Meta-Tags fuer Home-Screen/PWA-aehnliches Verhalten sind sinnvoll:
  - `apple-mobile-web-app-capable`
  - `apple-mobile-web-app-status-bar-style`
  - `viewport` mit mobilem Fokus
- Entscheidung: keine getrennte Codebasis "Desktop vs Mobile Homepage"; stattdessen eine Codebasis mit klar getrennten Views/Layouts pro Breakpoint und Phase.
- App-Skins/Visual-Ideen aus Referenzen nutzen, aber erst nach Abschluss der funktionalen Stabilitaet.

### 11.4 Hosting-Entscheidung (einfach, sicher, kostenlos)

Prioritaet fuer User ohne Server-Erfahrung:
1. **GitHub Pages + Supabase** (jetzt): am einfachsten, kostenlos, ausreichend fuer Training-V1.
2. **Render/Railway/Fly** (spaeter, falls FastAPI live benoetigt): einfacher als Oracle VM.
3. **Oracle VM**: leistungsfaehig und kostenlos moeglich, aber hoehere Komplexitaet (SSH, Linux, Nginx, Service-Management).

### 11.5 Reihenfolge der naechsten Arbeitspakete

1. Mobile Stabilitaet finalisieren (Timer-UX, Sortier-UX, Session-Fokus-Flow)
2. Dashboard-Training-Integration
3. FatSecret-Fixpaket
4. Security-Hardening fuer sensible Daten
5. Optional spaeter: Wirkstoff/Peptid-Rechner als separates Modul (nicht im Kern-Flow blockierend)

### 11.6 Letzter Umsetzungsschritt (14.04.2026)

#### ✅ Direkt umgesetzt in `training-preview.html`
- Geraetekatalog kann jetzt aus Supabase-Tabelle `ifl_device_catalog` laden (mit Fallback auf lokale Liste).
- Filter greifen fuer Hersteller / Zielmuskel / Session-Typ, Paging bleibt stueckweise (`Mehr laden`).
- Katalog-Buttons klarer getrennt: `+ Standard-Pool`, `+ Studio-Pool`, `+ Session`.
- Autosync nach lokalen Aenderungen aktiviert (DB, Session-Log, IFTTT-Events, Setup-Update).
- Strukturierter Sync erweitert: `notes` je Uebung werden mitgespeichert und wiederhergestellt.
- IFTTT-Daten werden im Sync mitgefuehrt; bei gesetztem Vault-Passwort verschluesselt als AES-GCM Blob.

#### 🔎 Hinweis fuer naechsten Testschritt
- In Supabase muss die Tabelle `ifl_device_catalog` vorhanden sein, damit Cloud-Katalog aktiv ist.
- Fuer verschluesselte Sync-Daten muss beim Download dasselbe `Vault-Passwort` gesetzt sein wie beim Upload.

#### 🔁 Nachtrag (14.04.2026, Katalog-UX)
- Sichtbarer Button `Cloud suchen` im Katalogbereich hinzugefuegt.
- Zusätzliche Statuszeile unter den Filtern zeigt jetzt klar:
  - Cloud-Katalog aktiv
  - oder Fallback auf lokale Katalogliste
  - oder Cloud-Fehlerhinweis (Tabelle/Key pruefen)

#### 🔁 Nachtrag (14.04.2026, Live-Katalog)
- Katalogsuche nutzt jetzt mehrstufig:
  1) Supabase `ifl_device_catalog` (falls befuellt)
  2) Live-Quellen online (gym80 WordPress Media + Wikimedia Commons)
  3) Lokaler Fallback-Katalog
- `Live suchen`-Button fragt explizit Online-Quellen ab und zeigt Treffer inkl. Bild.
- Treffer werden in das bestehende Uebungsformat gemappt und koennen direkt als
  `+ Standard-Pool`, `+ Studio-Pool` oder `+ Session` lokal gespeichert werden.

#### 🔁 Nachtrag (14.04.2026, Live-Treffer-Haertung)
- Wikimedia-Livesuche auf Datei-Namespace (`srnamespace=6`) umgestellt und Bild-URLs separat aufgeloest.
- Live-Suche erweitert um robusten Online-Fallback mit garantierten Vorschaubildern (`picsum`-Seed), damit Karten nicht leer bleiben.
- Bei Markenfilter (gym80/Matrix/eGym) liefert `Live suchen` jetzt auch dann Treffer, wenn externe Quellen temporär lückenhaft sind.

#### 🔁 Nachtrag (14.04.2026, Quellenbereinigung offiziell)
- Unbrauchbare Fremdquellen (Wikimedia/zufaellige Treffer) aus Live-Suche entfernt.
- Live-Suche nutzt jetzt nur markennahe/offizielle Quellen:
  - `gym80`: `wp-json/wp/v2/fitness_equipment` + zugehoerige Produkt-Medien
  - `Matrix`: offizieller `matrixhomefitness.com/products.json` Feed
  - `eGym`: offizielle Smart-Strength-Geraeteliste mit Branding-Bild von `us.egym.com`
- Harte Qualitaetsfilter aktiv (z. B. Ausschluss von PDF-/Brochure-/Accessory-Namen), damit keine fachfremden Treffer mehr angezeigt werden.

#### 🔁 Nachtrag (14.04.2026, Review + Fixrunde Katalog)
- Markenfilter-Haertung: Bei `eGym` werden nur eGym-Quellen abgefragt (gleiches fuer `gym80`/`Matrix`).
- Zusatzfilter fuer gym80 aktiv: Free-Weight-/Accessory-Titel wie `RPU BARBELL`, `Bumper`, `Hanger`, `Rack` werden ausgeschlossen.
- Matrix-Filter geschaerft: Shop-/Accessory-Produkte (`Lubricant`, `Pack`, `Storage`, etc.) werden ausgeschlossen; nur sinnvolle Geraeteeintraege bleiben.
- Mapping verbessert: Zielmuskel wird fuer Matrix zusaetzlich aus `product_type` abgeleitet, damit nicht alles pauschal als Brust erscheint.

#### 🔁 Nachtrag (14.04.2026, komplette Review Katalogpipeline)
- Live-Quellenabruf ist jetzt streng markenbasiert (`all` = alle Quellen, sonst nur gewaehlte Marke).
- gym80-Validierung erweitert um Kategorie-Filter via `equipment_category` Taxonomie (Accessories/Storage/Free Weights werden aktiv ausgeschlossen).
- Matrix-Validierung erweitert um Produkttyp/Tag-Whitelist + Blacklist, damit keine Shop-/Maintenance-Artikel in den Geraetekatalog rutschen.
- Suchpipeline intern geprueft: keine Lint-Fehler, Funktionen fuer Brand-Filter/Source-Filter/Quality-Filter konsistent vorhanden.

#### 🔁 Nachtrag (14.04.2026, Stabilitaet/Schnelligkeit Suche)
- Filter-Normalisierung vereinheitlicht (Umlaute/Sonderzeichen) fuer Brand/Target/Session-Typ/Suchtext.
- Markenabgleich auf exakte Canonical-Werte gehaertet (`gym80`/`matrix`/`egym`/`all`), keine unscharfen Includes mehr.
- Dedupe verbessert: bei Dubletten wird bevorzugt der Eintrag mit Bild behalten.
- Brand-Guard in Live-Fetches korrigiert (`all` funktioniert korrekt, Markenfilter bleibt strikt).

#### 🔁 Nachtrag (14.04.2026, UX + Diagnose Build)
- Katalog laedt jetzt **keine** Treffer mehr vor, solange kein Hersteller explizit gewaehlt ist.
- `Suchen` und `Live suchen` verlangen jetzt zuerst einen Hersteller; sonst klarer Hinweis im Katalog-Status.
- gym80 Live-Quelle erweitert: `fitness_equipment` wird ueber mehrere Seiten abgefragt (nicht nur erste Seite), um echte Maschinen zu finden.
- Matrix-Target-Mapping erweitert (`climb`/`climbmill` -> Beine) und Bench-Produkte als Nicht-Maschinen ausgeschlossen.
- Oben rechts neben `Training` wird jetzt ein Build-Label angezeigt (`Build YYYY-MM-DD HH:MM`) fuer sichere Versionskontrolle nach Hard-Refresh/GitHub-Update.

#### 🔁 Nachtrag (14.04.2026, Option B DB-Katalog aktiv)
- Neue DB-Entitaet `gym80_devices` in `app/models.py` aufgenommen (Zusatzpool-Katalog).
- Neuer Import-Service `app/services/gym80_catalog_import.py` erstellt:
  - liest `~/Downloads/gym80_devices.sql`
  - erstellt Tabelle bei Bedarf automatisch
  - importiert SQL und dedupliziert nach `(category, serie, model)`.
- Neue Import-Route in `app/routers/imports.py`:
  - `POST /import/gym80-catalog-import` fuer DB-Import
  - `GET /import/catalog/gym80` als API-Quelle fuer Zusatzpool-Suche.
- Import lokal ausgefuehrt: Ergebnis `before=0`, `after=82`, `imported=82`.

#### 🔁 Nachtrag (14.04.2026, Zusatzpool erweitert + Cardio)
- Neuer Sammel-Importservice `app/services/extra_catalog_import.py` erstellt fuer:
  - `gym80_devices`
  - `matrix_strength_devices`
  - `matrix_cardio_devices`
  - `egym_devices`
- Dedupe-Regel je Tabelle aktiv (behaelt pro `(category, serie/series, model)` nur einen Datensatz).
- Neue API-Routen:
  - `POST /import/catalog/import-extra` (Import aller SQL-Dateien aus `~/Downloads`)
  - `GET /import/catalog/search` (einheitliche Zusatzpool-Suche fuer Frontend)
- Import lokal getestet:
  - `gym80_devices`: 82
  - `matrix_strength_devices`: 16
  - `matrix_cardio_devices`: 15
  - `egym_devices`: 23
- `training-preview.html`:
  - Katalog-Livesuche nutzt jetzt DB-Endpoint `/import/catalog/search` statt fragiles Hersteller-Scraping.
  - Neuer Session-Reiter `Cardio` hinzugefuegt (Desktop + Mobile).
  - MyFitnessPal/IFTTT-Block aus Analyse entfernt.

