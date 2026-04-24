# Mobile Training UI - Umsetzungsliste

Stand: 2026-04-22

Diese Liste ist die verbindliche Arbeitsgrundlage fuer die naechsten Schritte an `training-preview.html` (GitHub Pages + Supabase-first).

## V1 - sofort umsetzen

- [x] 2-Tap Start Flow: Studio waehlen -> Training starten
- [x] Geraete nach Nutzungshaeufigkeit standardmaessig zuerst
- [x] Satz-Eingabe optimieren (grosse Touch-Felder, schneller Number-Flow)
- [x] One-Tap Repeat: letzten Satz uebernehmen
- [x] Letztes Training pro Satz sichtbar (Ghost Text)
- [x] Floating Rest Timer (immer sichtbar)
- [x] Undo nach Satz-Save (5 Sekunden)
- [x] Autosave nach jeder Satz-Eingabe
- [x] Klare Uebungszustaende: aktiv / pausiert / abgeschlossen
- [x] Sichtbarer Sync-Status: pending / ok / fehler
- [x] Grosse Touch-Ziele fuer Hauptaktionen im Session-Flow

## V1.1 - direkt danach

- [x] Studio Context Header immer sichtbar
- [x] Plan Day Card pro Session-Tag (Push/Pull/Legs/Cardio/Frei)
- [x] Uebung schnell ueberspringen ohne Datenverlust
- [x] DB-Suche als Bottom-Sheet fuer mobile Nutzung
- [x] Uebung austauschen direkt aus DB-Suche
- [x] Filter-Presets (Marke/Zielmuskel/Sessiontyp)
- [x] Session Progress Rail (z. B. Uebung 3/8, Satz 2/4)
- [~] Sofortige lokale UI-Reaktion, dann Cloud-Sync
- [x] Kein Pflicht-Modal waehrend laufender Session

## V2+ - spaetere Ausbaustufe

- [~] Recent/Frequent Split als zusaetzlicher Modus
- [x] RPE Quick Chips
- [~] Image-first Device Tiles weiter verfeinern
- [x] In-Session Notes Micro
- [ ] Offline Queue fuer komplette Session-Logs
- [x] Post-Workout Summary (Volumen, PRs, Bestsatz)
- [x] Bilder lazy laden, Texte zuerst
- [x] Bild-Fallback pro Karte (nie ganze Liste verlieren)

## Betriebsregeln waehrend Umsetzung

- Nach jedem inhaltlichen Block: `BUILD_STAMP` in `training-preview.html` aktualisieren.
- Nach jedem Block: Commit + Push auf `main`.
- Nach jedem Push: Live-Check auf GitHub Pages gegen `BUILD_STAMP`.
- Keine lokalen-only Abhaengigkeiten fuer den mobilen Training-Flow.
