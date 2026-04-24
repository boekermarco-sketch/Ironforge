# HARD PRUEFMODUS (verbindlich)

Stand: 2026-04-23

Diese Regeln gelten ab sofort fuer alle Aufgaben in diesem Projektchat.

## Pflicht vor jeder "fertig"-Meldung

1. Vollstaendige Selbstpruefung:
   - Code-Review auf Logik, Nebenwirkungen, Regressionen
   - Edge-Case-Check fuer relevante Grenzfaelle
2. Syntax/Lint/Tests ausfuehren
   - oder klar dokumentieren, warum lokal nicht ausfuehrbar
3. Kritische Stellen gezielt verifizieren
   - z. B. Formeln, Dateizugriffe, Exporte, Layout/Renderpfade, Deploy-Pfade
4. Konkrete Pruefergebnisse berichten
   - was geprueft wurde
   - wie geprueft wurde
   - Ergebnis pro Check
5. Restrisiken offen benennen
   - keine impliziten Annahmen verschweigen

## Verboten

- Kein "sollte passen" ohne Nachweis
- Kein Abschluss ohne reproduzierbaren Testlauf plus gezielte Zusatzchecks
- Keine Freigabe bei Unsicherheit ohne weitere Analyse/Fix
