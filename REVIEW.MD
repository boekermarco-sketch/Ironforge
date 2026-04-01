# REVIEW.md – Code-Review-Regeln für dieses Projekt

Dieses Dokument definiert **spezifische Regeln für Code-Reviews** in diesem Projekt. Es ergänzt `CLAUDE.md` und definiert genau, was beim Review geprüft wird, wie Findings klassifiziert werden und welche Grenzen gelten.

---

## 1. Ziel des Reviews

Das Review soll sicherstellen, dass der Code:

- korrekt funktioniert
- sicher ist
- performant ist
- wartbar und erweiterbar bleibt
- gut dokumentiert ist
- konsistent mit der bestehenden Architektur bleibt

---

## 2. Prüfkriterien (Pflicht-Checkliste)

Jedes Review muss folgende Aspekte explizit prüfen:

### 2.1 Korrektheit

- Funktionalität entspricht Anforderungen
- Keine logischen Fehler
- Keine unbeabsichtigten Seiteneffekte
- Korrekte Behandlung von Edge Cases
- Korrekte Validierung von Eingaben

### 2.2 Architektur & Modularität

- Klare Trennung der Verantwortlichkeiten
- Geringe Kopplung zwischen Modulen
- Hohe Kohäsion innerhalb von Modulen
- Keine God-Classes / God-Functions
- Sinnvolle Aufteilung in Dateien/Module
- Widerspruch frei zur bestehenden Architektur

### 2.3 Lesbarkeit & Wartbarkeit

- Spreuende, klare Namen (Variablen, Funktionen, Klassen, Module)
- Kleine, fokusierte Funktionen/Methoden
- Vermeidung von Code-Duplikation (DRY)
- Nachvollziehbare Struktur
- Keine unnötige Komplexität
- Konsistenz mit bestehendem Stil (sofern dieser nicht klar problematisch ist)

### 2.4 Fehlerbehandlung

- Korrekte Fehlerbehandlung und -weitergabe
- Sinnvolle Fehlermeldungen
- Keine leeren catch-Blöcke ohne Begründung
- Erlaubte Error-Logging/Handling-Strategien eingehalten
- Graceful Degradation /Fallback-Szenarien wo nötig

### 2.5 Sicherheit

- Keine offensichtlichen Sicherheitslücken (Injection, XSS, CSRF, etc.)
- Sensible Daten (Passwörter, Keys, Tokens) nicht hardcoded
- Sichere Default-Werte
- Validierung und Sanitization von Eingaben
- Berechtigungen und Zugriffschecks wo nötig

### 2.6 Performance

- Keine offensichtlich ineffizienten Algorithmen
- Keine unnötigen Schleifen, Abfragen, Kopien
- Angemessene Nutzung von Ressourcen
- Wo sinnvoll: Caching-Strategien
- Keine Blockierung von wichtigen Threads/Links

### 2.7 Testbarkeit & Tests

- Code ist testbar (kleine, abgegrenzte Einheiten, klare Schnittstellen)
- Wo relevant: esistende Tests vorhanden und korrekt
- Bei neuen/geänderten Logik: Tests ergänzt oder konkrete Testvorschläge gemacht
- Edge Cases durch Tests abgedeckt wo sinnvoll

### 2.8 Dokumentation

- In-Code-Dokumentation dort, wo Absicht nicht offensichtlich ist
- README / Architektur-Doku aktualisiert wo nötig
- API-Schnittstellen dokumentiert
- Entscheidungsgrundlagen nachvollziehbar dokumentiert
- Keine veralteten Kommentare

---

## 3. Klassifizierung von Findings

Jedes Finding muss in eine Kategorie eingeteilt werden:

### Kritisch (Muss behoben werden)

- Fachliche Fehler
- Logikfehler
- Sicherheitslücken
- Datenkorruptions-Risiken
- Funktionsuntüchtigkeit unter bestimmten Bedingungen

### Wichtig (Umgangsfest behoben oder begründet ausgenommen)

- Wartbarkeit-Probleme
- Fehlende Fehlerbehandlung
- Performance-Probleme mit spürbarem Einfluss
- Fehlende Tests bei kritischer Logik
- Fehlende Dokumentation bei wichtigen Teilen

### Optional (Kann behoben werden)

- Stilfragen
- Kleine Verbesserungen
- “Nice-to-have”-Refactors
- Lesenbarkeits-Optimierungen ohne funktionale Auswirkung

---

## 4. Scope & Grenzen des Reviews

- Nur geänderte/geplante Bereiche werden tief geprüft.
- **Unbeteiligte Bereiche werden nicht “im Vorbeigehen” umgebaut**.
- Kosmetische Massenänderungen ohne klaren Nutzen sind verboten.
- Große Refactors außerhalb des Scopes müssen explizit als separate Aufgabe vorgeschlagen werden.
- Bei Änderungen außerhalb des Scopes: **erst explizite Zustimmung** einholen.

---

## 5. Evidence-Regel

Bei jedem relevanten Finding muss möglichst angegeben werden:

- Datei
- Modul / Klasse / Funktion
- Zeilenbereich (wenn möglich)
- Ursache
- Auswirkung

Beispiel:
```text
Kritisch – security/validation
Datei: src/api/handler.ts
Funktion: handleUserInput
Problem: Benutzer-Eingabe wird nicht sanitisiert vor DB-Abfrage verwendet.
Auswirkung: Potenzielle SQL-Injection.
