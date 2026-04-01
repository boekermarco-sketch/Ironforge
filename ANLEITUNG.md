# Fitness Dashboard – Bedienungsanleitung
## Marco Böker | Persönliches Gesundheits-Dashboard

Stand: 01.04.2026

---

## INHALTSVERZEICHNIS

1. [App starten und beenden](#1-app-starten-und-beenden)
2. [Dashboard – die Startseite](#2-dashboard)
3. [Tageslog – Garmin & Körperdaten eintragen](#3-tageslog)
4. [Freitag Check-in – Wochendaten erfassen](#4-freitag-check-in)
5. [Blutbilder – PDF einlesen und auswerten](#5-blutbilder)
6. [Stack – Substanzen und Dosierungen verwalten](#6-stack)
7. [Journal – Fotos und KI-Analysen speichern](#7-journal)
8. [Ereignisse – Aderlass und Arzttermine](#8-ereignisse)
9. [Import – Withings, Garmin, MyFitnessPal](#9-import)
10. [Häufige Fragen und Probleme](#10-faq)
11. [Daten sichern](#11-daten-sichern)

---

## 1. App starten und beenden

### Starten
1. Ordner `C:\Users\boeke\Meine Ablage\ClaudeAI\Fitness` öffnen
2. Doppelklick auf **`start.bat`**
3. Ein schwarzes Fenster öffnet sich – das ist der Server
4. Browser öffnet sich automatisch auf `http://localhost:8080`
5. Wenn der Browser nicht automatisch öffnet: manuell `http://localhost:8080` eingeben

> **Wichtig:** Das schwarze Fenster darf NICHT geschlossen werden, solange du die App nutzt.
> Es ist der Motor der App. Minimieren ist OK.

### Beenden
1. Schwarzes Fenster in den Vordergrund holen
2. `Strg + C` drücken
3. Fenster schließt sich automatisch

### Beim nächsten Start
Einfach wieder `start.bat` doppelklicken. Alle deine Daten sind gespeichert in `fitness.db`.

---

## 2. Dashboard

Die Startseite zeigt dir auf einen Blick:

| Kachel | Was du siehst |
|---|---|
| **Gewicht** | Letzter eingetragener Wert + Datum |
| **HRV** | Letzter Wert + Ampel (grün = >32ms, gelb = 28-32ms, rot = <28ms) |
| **Schlaf-Score** | Letzter Garmin-Score |
| **Body Battery** | Letzter Garmin-Wert |
| **Aktiver Stack** | Name, Fortschrittsbalken, kritische Blutwerte |
| **Letztes Blutbild** | Datum + direkter Link zur Auswertung |
| **HRV & Gewicht Chart** | Verlauf der letzten 30 Tage |
| **Letztes Ereignis** | Letzter Aderlass oder Arzttermin |
| **Journal** | Die 3 letzten Einträge |

### Was tun wenn Daten fehlen?
- Kacheln zeigen "–" wenn noch kein Eintrag vorhanden
- Tageslog ausfüllen → Kacheln aktualisieren sich sofort
- Nach jedem Freitag Check-in ist das Dashboard auf dem neuesten Stand

---

## 3. Tageslog

Navigationspunkt: **Tageslog**

Hier trägst du täglich (oder nach jedem Garmin-Sync) deine Werte ein.

### Eintrag erstellen
1. Klicke auf **Tageslog** in der Navigation
2. Das Formular links ist bereits auf das heutige Datum voreingestellt
3. Felder ausfüllen (nur die Felder die du hast – leere Felder sind OK)
4. Klicke **Eintrag speichern**

### Welche Felder woher kommen

**Garmin (von der Garmin Connect App oder Uhr ablesen):**
- HRV (ms) → Garmin Connect App → Herzfrequenzvariabilität
- HF Nacht (bpm) → Durchschnittliche Herzfrequenz Schlafphase
- Schlaf-Score → Garmin Schlafübersicht
- Tiefschlaf (Min) → Garmin Schlafphasen
- REM (Min) → Garmin Schlafphasen
- Gesamtschlaf (Min) → z.B. 7h15min = 435 Min
- Body Battery → Garmin Startseite
- Atemfrequenz (brpm) → Garmin Schlafübersicht

**Körper (Withings Waage + manuell):**
- Gewicht (kg) → Withings Waage, nüchtern nach Toilette
- KFA % → Withings Waage Messung

**Subjektiv (Skala 1-10):**
- Energie, Libido, Stimmung, Trainingsgefühl → 1 = sehr schlecht, 10 = perfekt
- Wasserretention, Akne → 1 = keine, 5 = stark
- Nachtschweiß → Dropdown: nein / weniger / ja
- Trainings-Einheiten → Anzahl Trainings diese Woche

### Charts rechts
Die drei Charts (HRV, Gewicht, Schlaf-Score) zeigen automatisch die letzten 30 Tage.
Sie aktualisieren sich nach jedem neuen Eintrag beim nächsten Laden der Seite.

### Vergangenes Datum nachtragen
Das Datums-Feld kann geändert werden. Einfach das gewünschte Datum eingeben.
Wenn für dieses Datum bereits ein Eintrag existiert, wird er überschrieben.

---

## 4. Freitag Check-in

Das Freitag-Check-in nutzt dasselbe Tageslog-Formular – alle Felder aus deinem
Check-in-Template (Übergabe_Protokoll.md Abschnitt 12) sind vorhanden.

### Ablauf jeden Freitag
1. Garmin Connect App öffnen → alle Werte ablesen
2. `start.bat` starten → Browser auf `http://localhost:8080/tageslog/`
3. Formular ausfüllen (Freitagsdatum eingetragen lassen)
4. **Eintrag speichern**
5. Dann: **Journal** → **Neuer Eintrag**
6. Typ: **Check-in** wählen
7. Titel: z.B. "Freitag Check-in KW14 – Post-Aderlass"
8. Analyse/KI-Meinung: Claude-Zusammenfassung aus dem Chat hier einfügen
9. Speichern → bleibt dauerhaft in der Timeline

---

## 5. Blutbilder

Navigationspunkt: **Blutbilder**

### Blutbild-PDF automatisch einlesen (empfohlen)

**Methode A – Direkt hochladen:**
1. Klicke auf **Blutbilder** in der Navigation
2. Klicke auf **Datei auswählen** unter "PDF hochladen"
3. Dein PDF vom Labor auswählen (z.B. Befund_01042026.pdf)
4. Klicke **Parsen & speichern**
5. Du wirst automatisch zur Auswertung weitergeleitet

**Methode B – Ordner ablegen:**
1. PDF in den Ordner `data\Blutbilder\` kopieren
2. In der App: **Import** → **Ordner jetzt scannen**
3. Alle neuen PDFs werden automatisch eingelesen

### Blutbild-Auswertung lesen

Nach dem Einlesen siehst du eine farbige Tabelle:

| Farbe | Bedeutung |
|---|---|
| 🟢 Grün | Wert im Normbereich |
| 🟡 Gelb | Grenzwertig (außerhalb Optimalbereich) |
| 🔴 Rot | Kritisch – außerhalb Referenzbereich |

- **Trend-Pfeile** (↑↓) zeigen Vergleich zum vorherigen Blutbild
- Die Werte sind nach Kategorien gruppiert (Hormone, Leber, Blutbild, etc.)

### Fehlende Werte manuell ergänzen
Falls der PDF-Parser einen Wert nicht erkannt hat:
1. Auf das Blutbild klicken
2. Ganz unten: "+ Wert manuell hinzufügen"
3. Marker aus Dropdown wählen, Wert eingeben, speichern

### Verlaufs-Diagramm
Auf der Blutbild-Übersichtsseite unten:
1. Marker aus Dropdown wählen (z.B. "Estradiol")
2. Chart zeigt alle bisherigen Werte über Zeit
3. Rote Linien = Referenzbereich

### Für das heutige Blutbild (01.04.2026)
PDF vom Labor → in `data\Blutbilder\` legen → **Import** → **Ordner scannen**
Oder direkt über Blutbilder-Seite hochladen.

---

## 6. Stack

Navigationspunkt: **Stack**

Dein aktueller Stack (Stand 25.03.2026) ist bereits vollständig vorausgefüllt mit
allen 41 Substanzen und 35 aktiven Dosierungen.

### Was du siehst
- Alle aktiven Substanzen gruppiert nach Kategorie (Steroid, Peptid, Medikament, Supplement, Hormon)
- Dosis, Frequenz, Timing, Startdatum für jede Substanz

### Dosierung ändern (z.B. Anavar starten nach Blutbild)
Eine Dosisänderung wird NIEMALS überschrieben – stattdessen:

1. Alte Dosierung beenden: Klick auf **✕** bei der bisherigen Dosis
   (Bestätigung → wird mit heutigem Datum beendet)
2. Neue Dosierung anlegen: Formular "Dosierung hinzufügen" ausfüllen
   - Substanz wählen (z.B. Anavar)
   - Neue Dosis eingeben (z.B. 50 mg)
   - Startdatum: heute
   - Grund: "Nach Blutbild 01.04 – GPT <50"
3. Speichern

So bleibt der vollständige Verlauf aller Dosierungsänderungen erhalten.

### Neue Substanz anlegen
Ganz unten auf der Stack-Seite: Formular "+ Neue Substanz anlegen"
Name, Kategorie, Route (oral/subkutan/intramuskulär), Einheit eingeben → Speichern.
Danach kann die Substanz im Dosierungs-Formular ausgewählt werden.

---

## 7. Journal

Navigationspunkt: **Journal**

Das Journal ist dein persönliches Gedächtnis. Alles was du mit Claude besprichst
und nicht verlieren willst, kommt hier rein.

### Neuen Eintrag anlegen
1. Klicke **+ Neuer Eintrag** (oben rechts)
2. Felder ausfüllen:
   - **Datum** → wird automatisch auf heute gesetzt
   - **Uhrzeit** → optional
   - **Titel** → kurze Beschreibung (z.B. "Blutbild 01.04.2026 Auswertung")
   - **Typ** → passenden Typ wählen:
     - `Fortschrittsfoto` → wöchentliches Foto
     - `Blutbild` → Auswertung oder KI-Analyse
     - `Garmin` → besondere Garmin-Werte
     - `Check-in` → Freitag Check-in
     - `Allgemein` → alles andere
   - **Bild oder PDF** → Foto oder PDF hochladen (optional)
   - **Analyse / KI-Meinung** → hier Claude's Antwort aus dem Chat einfügen
   - **Gewicht / KFA** → optionale Schnappschuss-Daten zum Zeitpunkt
   - **Tags** → z.B. "Blutbild, Aderlass, Woche 6" (kommagetrennt)
3. Klicke **Eintrag speichern**

### Workflow: Foto + Claude-Analyse speichern
1. Foto in Claude hochladen → Analyse erhalten
2. In Journal → Neuer Eintrag
3. Typ: Fortschrittsfoto
4. Bild hochladen (das gleiche Foto)
5. Claude's Analyse-Text in "Analyse / KI-Meinung" einfügen
6. Speichern → dauerhaft in der Timeline

### Timeline filtern
Oben auf der Journal-Seite: Buttons für jeden Typ
Klicke z.B. auf **Fortschrittsfoto** → nur Fotos werden angezeigt
Klicke auf **Alle** → alle Einträge wieder sichtbar

### Eintrag löschen
**✕** Button oben rechts im Eintrag → Bestätigung → gelöscht (inkl. Bild)

---

## 8. Ereignisse

Navigationspunkt: **Ereignisse**

### Aderlass oder Blutspende eintragen
1. Klicke **Ereignisse**
2. Formular links ausfüllen:
   - **Datum** → Datum des Aderlasses/der Blutspende
   - **Typ** → Dropdown: **Aderlass** oder **Blutspende** wählen
     - *Aderlass* = therapeutisch, Blut wird verworfen (wegen Stack nicht verwendbar)
     - *Blutspende* = Blut wird gespendet/gelagert
   - **Menge in ml** → z.B. 450
   - **Ort** → z.B. "Blutspendezentrum Bremen"
   - **Notizen** → z.B. "Danach Clen auf 40mcg, Hämatokrit war 0,53"
3. **Speichern**

> Dein erster Aderlass vom **30.03.2026** ist bereits eingetragen.

### Weitere Ereignis-Typen
- **Arzttermin** → mit Ort und Notizen
- **Impfung** → mit Notizen
- **Sonstiges** → für alles andere

---

## 9. Import

Navigationspunkt: **Import**

### Withings CSV importieren

**Schritt 1 – Export von Withings anfordern:**
1. Browser öffnen → `account.withings.com`
2. Einloggen
3. Klicke auf **Datenschutz** (links im Menü)
4. Klicke auf **Meine persönlichen Daten herunterladen**
5. Du erhältst eine E-Mail mit einem ZIP-Link (dauert ca. 10-30 Minuten)
6. ZIP herunterladen und entpacken

**Schritt 2 – In der App importieren:**
1. In der App: **Import** klicken
2. Unter "Withings": **Datei auswählen**
3. Die CSV-Datei aus dem Withings-ZIP auswählen (meist `weight.csv` oder ähnlich)
4. Klicke **Withings importieren**
5. Erfolgsmeldung zeigt: X neue Einträge, Y aktualisiert

### Garmin CSV importieren

**Schritt 1 – Export von Garmin anfordern:**
1. Browser öffnen → `connect.garmin.com`
2. Einloggen
3. Profilbild oben rechts → **Konto**
4. **Daten exportieren** → Anfrage stellen
5. Du erhältst eine E-Mail (dauert bis zu 24 Stunden)
6. ZIP herunterladen und entpacken

**Schritt 2 – In der App importieren:**
1. In der App: **Import** klicken
2. Unter "Garmin Connect": **Datei auswählen**
3. CSV aus dem Garmin-ZIP auswählen
4. Klicke **Garmin importieren**

### Blutbild-PDFs aus Ordner scannen
1. PDF-Datei(en) in den Ordner `data\Blutbilder\` kopieren
2. In der App: **Import** → **Ordner jetzt scannen**
3. Neue PDFs werden automatisch erkannt und eingelesen
4. Bereits eingelesene PDFs werden nicht doppelt importiert

---

## 10. FAQ

**F: Wo sind meine Daten gespeichert?**
A: In der Datei `fitness.db` im Projektordner. Diese eine Datei enthält alles.
Für ein Backup einfach diese Datei kopieren.

**F: Was passiert wenn ich `fitness.db` lösche?**
A: Alle manuell eingegebenen Daten gehen verloren. Beim nächsten Start werden
die Seed-Daten (dein Stack, die ersten zwei Blutbilder, Garmin-Verlauf bis 24.03)
automatisch neu geladen. Deshalb: Regelmäßig sichern!

**F: Der PDF-Parser hat nicht alle Werte erkannt – was tun?**
A: Fehlende Werte manuell ergänzen: Blutbild öffnen → "+ Wert manuell hinzufügen".
Wenn ein Laborname regelmäßig nicht erkannt wird, Claude Bescheid geben –
ich ergänze den Alias im Parser.

**F: Ich will eine Dosierung rückwirkend korrigieren**
A: Die alte Dosierung mit ✕ beenden (Datum anpassen), neue korrekte anlegen.
So bleibt die Historie korrekt.

**F: Kann ich die App auf dem Handy nutzen?**
A: Im gleichen WLAN-Netz: `http://[PC-IP-Adresse]:8080` im Handy-Browser aufrufen.
PC-IP findest du mit: Windows-Taste → cmd → `ipconfig` → IPv4-Adresse.

**F: Was tun bei "Port belegt" Fehler?**
A: Das schwarze Fenster vom letzten Start ist noch offen. Schließen, dann neu starten.
Oder: `start.bat` enthält bereits eine automatische Port-Bereinigung.

**F: Wie erkenne ich ob neue Daten importiert wurden?**
A: Im Dashboard: Gewicht, HRV-Kacheln zeigen das aktuellste Datum.
Im Tageslog: Tabelle unten zeigt alle Einträge chronologisch.

**F: Kann Claude direkt auf die App zugreifen?**
A: Noch nicht. Aktuell: Daten in Claude eingeben → Analyse erhalten →
Analyse im Journal speichern. Automatische Integration ist für Phase 3 geplant.

---

## 11. Daten sichern

### Manuelles Backup (empfohlen: 1x/Woche)
1. App beenden (Strg+C im schwarzen Fenster)
2. Datei `fitness.db` kopieren
3. In einen sicheren Ordner einfügen (z.B. Google Drive, OneDrive)
4. Empfehlung: Datum im Dateinamen, z.B. `fitness_backup_20260401.db`

### Wiederherstellen nach Datenverlust
1. App beenden
2. Backup-Datei in den Projektordner kopieren
3. In `fitness.db` umbenennen
4. App neu starten

### Was gesichert wird (alles in `fitness.db`)
- Alle eingetragenen Blutbilder + Werte
- Stack, Substanzen, Dosierungshistorie
- Tages-Logs (Garmin + Withings + manuell)
- Journal-Einträge + Analyse-Texte
- Medizinische Ereignisse

> **Fotos** liegen separat in `data\Fortschritt_Fotos\` – diesen Ordner ebenfalls sichern!

---

## Schnell-Referenz: Wöchentlicher Workflow

```
Jeden Tag (morgens):
→ Garmin-Werte ablesen → Tageslog eintragen
→ Withings Waage nutzen → Gewicht/KFA notiert sich

Jeden Freitag:
→ Tageslog vollständig ausfüllen (Check-in Template)
→ Journal → Neuer Eintrag (Typ: Check-in)
→ Ggf. Foto hochladen + Claude-Analyse einfügen

Bei neuem Blutbild:
→ PDF vom Labor → data\Blutbilder\ ablegen
→ Import → Ordner scannen
→ Auswertung prüfen, fehlende Werte ergänzen
→ Journal-Eintrag mit Analyse anlegen

Bei Dosisänderung:
→ Stack → alte Dosis mit ✕ beenden
→ Neue Dosierung hinzufügen mit Startdatum + Grund
```

---

*Bei Fragen oder Problemen: Dieses Dokument + ARCHITECTURE.md an Claude schicken
und konkrete Frage stellen. Claude hat den vollständigen Kontext.*
