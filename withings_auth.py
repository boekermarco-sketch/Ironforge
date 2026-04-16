"""
Einmalige Withings OAuth-Authentifizierung.
Führe dieses Skript einmalig aus um .withings_credentials.json zu erstellen.

Vorbereitung im Withings Developer Portal (developer.withings.com):
  1. Anmelden → "My Apps" → "Create Application"
  2. App-Typ: "Public API"
  3. Redirect URI eintragen: http://localhost:8090
  4. CLIENT_ID und CLIENT_SECRET in .env eintragen:
       WITHINGS_CLIENT_ID=...
       WITHINGS_CLIENT_SECRET=...

Dann dieses Skript ausführen:
  python withings_auth.py
"""
import os
import json
import time
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import requests

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CLIENT_ID = os.getenv("WITHINGS_CLIENT_ID")
CLIENT_SECRET = os.getenv("WITHINGS_CLIENT_SECRET")
CALLBACK_URL = "http://localhost:8090"
CREDS_FILE = BASE_DIR / ".withings_credentials.json"

AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("\nFEHLER: WITHINGS_CLIENT_ID oder WITHINGS_CLIENT_SECRET fehlen in .env")
        print("Trage die Werte aus dem Withings Developer Portal ein.")
        return

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "state": "fitness_app",
        "scope": "user.metrics,user.activity",
        "redirect_uri": CALLBACK_URL,
    })
    url = f"{AUTH_URL}?{params}"

    print("\n" + "=" * 65)
    print("SCHRITT 1: Öffne diesen Link im Browser:")
    print()
    print(url)
    print()
    print("=" * 65)
    print()
    print("SCHRITT 2: Melde dich bei Withings an und erteile Zugriff.")
    print()
    print("SCHRITT 3: Du wirst zu http://localhost:8090 weitergeleitet.")
    print("  Der Browser zeigt einen Verbindungsfehler – das ist normal.")
    print("  Schau in die Adressleiste. Dort steht z.B.:")
    print("    http://localhost:8090?code=DEINCODE&state=...")
    print()
    print("  Kopiere nur den Wert nach 'code=' (bis zum nächsten '&').")
    print()

    code = input("Code hier einfügen und Enter drücken: ").strip()
    if not code:
        print("Kein Code eingegeben – abgebrochen.")
        return

    try:
        resp = requests.post(TOKEN_URL, data={
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": CALLBACK_URL,
        }, timeout=15)
        data = resp.json()

        if data.get("status") != 0:
            print(f"\nFEHLER von Withings (status={data.get('status')}): {data.get('error', 'Unbekannter Fehler')}")
            print("Prüfe ob CLIENT_ID/SECRET korrekt sind und ob der Code noch gültig ist.")
            return

        body = data["body"]
        creds = {
            "access_token": body["access_token"],
            "refresh_token": body["refresh_token"],
            "expires_at": int(time.time()) + int(body.get("expires_in", 10800)),
            "userid": body.get("userid"),
        }
        with open(CREDS_FILE, "w") as f:
            json.dump(creds, f, indent=2)

        print(f"\nErfolgreich! Credentials gespeichert: {CREDS_FILE}")
        print("Du kannst jetzt in der App unter Import → 'Heute abrufen' klicken.")

    except Exception as e:
        print(f"\nFEHLER: {e}")


if __name__ == "__main__":
    main()
