# Mobile Training UI - Umsetzungsliste

Stand: 2026-04-22

Diese Liste ist die verbindliche Arbeitsgrundlage fuer die naechsten Schritte an `training-preview.html` (GitHub Pages + Supabase-first).

## V1 - sofort umsetzen

- [ ] 2-Tap Start Flow: Studio waehlen -> Training starten
- [ ] Geraete nach Nutzungshaeufigkeit standardmaessig zuerst
- [ ] Satz-Eingabe optimieren (grosse Touch-Felder, schneller Number-Flow)
- [ ] One-Tap Repeat: letzten Satz uebernehmen
- [ ] Letztes Training pro Satz sichtbar (Ghost Text)
- [ ] Floating Rest Timer (immer sichtbar)
- [ ] Undo nach Satz-Save (5 Sekunden)
- [ ] Autosave nach jeder Satz-Eingabe
- [ ] Klare Uebungszustaende: aktiv / pausiert / abgeschlossen
- [ ] Sichtbarer Sync-Status: pending / ok / fehler
- [ ] Grosse Touch-Ziele fuer Hauptaktionen im Session-Flow

## V1.1 - direkt danach

- [ ] Studio Context Header immer sichtbar
- [ ] Plan Day Card pro Session-Tag (Push/Pull/Legs/Cardio/Frei)
- [ ] Uebung schnell ueberspringen ohne Datenverlust
- [ ] DB-Suche als Bottom-Sheet fuer mobile Nutzung
- [ ] Uebung austauschen direkt aus DB-Suche
- [ ] Filter-Presets (Marke/Zielmuskel/Sessiontyp)
- [ ] Session Progress Rail (z. B. Uebung 3/8, Satz 2/4)
- [ ] Sofortige lokale UI-Reaktion, dann Cloud-Sync
- [ ] Kein Pflicht-Modal waehrend laufender Session

## V2+ - spaetere Ausbaustufe

- [ ] Recent/Frequent Split als zusaetzlicher Modus
- [ ] RPE Quick Chips
- [ ] Image-first Device Tiles weiter verfeinern
- [ ] In-Session Notes Micro
- [ ] Offline Queue fuer komplette Session-Logs
- [ ] Post-Workout Summary (Volumen, PRs, Bestsatz)
- [ ] Bilder lazy laden, Texte zuerst
- [ ] Bild-Fallback pro Karte (nie ganze Liste verlieren)

## Betriebsregeln waehrend Umsetzung

- Nach jedem inhaltlichen Block: `BUILD_STAMP` in `training-preview.html` aktualisieren.
- Nach jedem Block: Commit + Push auf `main`.
- Nach jedem Push: Live-Check auf GitHub Pages gegen `BUILD_STAMP`.
- Keine lokalen-only Abhaengigkeiten fuer den mobilen Training-Flow.
