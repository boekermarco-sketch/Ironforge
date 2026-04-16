"""
FatSecret OAuth 1.0 – 3-Legged Authentication (kostenlos, für Food Diary).
Legt .fatsecret_credentials.json im Projektordner an.

Vorbereitung auf https://platform.fatsecret.com/api/:
  1. Einloggen → "My Account" → Application auswählen → Consumer Key + Secret kopieren
  2. In .env eintragen:
       FATSECRET_CLIENT_ID=dein_consumer_key
       FATSECRET_CLIENT_SECRET=dein_consumer_secret

Dann ausführen:
  python fatsecret_auth.py

Der Browser öffnet die FatSecret-Autorisierungsseite. Nach Bestätigung
wird der Verifier automatisch über einen lokalen Server abgefangen.
FatSecret OAuth 1.0 Tokens laufen nicht ab — einmalige Einrichtung.
"""
import os
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from requests_oauthlib import OAuth1Session

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*a, **kw): pass

BASE_DIR   = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CONSUMER_KEY    = os.getenv("FATSECRET_CLIENT_ID", "")
CONSUMER_SECRET = os.getenv("FATSECRET_CLIENT_SECRET", "")
CALLBACK_URL    = "http://localhost:8765/callback"
CREDS_FILE      = BASE_DIR / ".fatsecret_credentials.json"

REQUEST_TOKEN_URL = "https://platform.fatsecret.com/rest/oauth/request_token"
AUTHORIZE_URL     = "https://www.fatsecret.com/oauth/authorize"
ACCESS_TOKEN_URL  = "https://platform.fatsecret.com/rest/oauth/access_token"

received_params = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        received_params.update(params)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"""
            <html><body style="font-family:sans-serif;padding:40px;background:#0a0a0a;color:#fbf7ef">
            <h2 style="color:#d0a35a">FatSecret Autorisierung erfolgreich!</h2>
            <p>Dieses Fenster kann geschlossen werden.</p>
            </body></html>
        """)

    def log_message(self, *args):
        pass  # Kein Logging


def main():
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        print("\nFEHLER: FATSECRET_CLIENT_ID oder FATSECRET_CLIENT_SECRET fehlen in .env")
        print("\nSo findest du die Credentials:")
        print("  1. https://platform.fatsecret.com/api/ aufrufen")
        print("  2. Einloggen → 'My Account' oder 'My Applications'")
        print("  3. Deine App anklicken → Consumer Key + Consumer Secret kopieren")
        return

    print("\n" + "=" * 60)
    print("FatSecret – 3-Legged OAuth 1.0 Autorisierung")
    print("=" * 60)

    # Schritt 1: Request Token holen
    print("\n[1/3] Request Token wird abgerufen...")
    try:
        oauth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            callback_uri=CALLBACK_URL,
        )
        r = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    except Exception as e:
        print(f"\nFEHLER beim Request Token: {e}")
        print("Prüfe ob CONSUMER_KEY und CONSUMER_SECRET korrekt sind.")
        return

    resource_owner_key    = r["oauth_token"]
    resource_owner_secret = r["oauth_token_secret"]

    # Schritt 2: Browser mit Autorisierungs-URL öffnen
    auth_url = f"{AUTHORIZE_URL}?oauth_token={resource_owner_key}"
    print(f"\n[2/3] Autorisierungs-URL:")
    print(f"\n  >>> {auth_url} <<<\n")
    print("      Bitte diese URL im Browser öffnen, einloggen und Zugriff erlauben.")
    opened = webbrowser.open(auth_url)
    if not opened:
        print("      (Browser konnte nicht automatisch geöffnet werden – URL oben manuell kopieren)")

    # Schritt 3: Callback abwarten (lokaler Server) ODER manuell eingeben
    print(f"\n[3/3] Warte auf Callback auf localhost:8765 ...")
    print("      (Nach Bestätigung im Browser wird der Verifier automatisch abgefangen)")
    print("      Falls das nicht klappt: Callback-URL aus dem Browser kopieren und unten eingeben.\n")

    verifier = None
    try:
        server = HTTPServer(("localhost", 8765), CallbackHandler)
        server.handle_request()
        print(f"\nCallback empfangen. Parameter: {received_params}")
        verifier = received_params.get("oauth_verifier")
    except OSError as e:
        print(f"Port 8765 nicht verfügbar: {e}")

    if not verifier:
        print("\nVerifier nicht automatisch empfangen.")
        print("Bitte die vollständige Callback-URL aus dem Browser kopieren")
        print("(sieht aus wie: http://localhost:8765/callback?oauth_token=...&oauth_verifier=XXXXX)")
        raw = input("Callback-URL oder nur den oauth_verifier-Wert eingeben: ").strip()
        if "oauth_verifier=" in raw:
            verifier = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(raw).query)).get("oauth_verifier", "")
        else:
            verifier = raw

    if not verifier:
        print("\nFEHLER: Kein Verifier – Abbruch.")
        return

    # Schritt 4: Access Token tauschen
    print("\nAccess Token wird abgerufen...")
    try:
        oauth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    except Exception as e:
        print(f"\nFEHLER beim Access Token: {e}")
        return

    creds = {
        "consumer_key":    CONSUMER_KEY,
        "consumer_secret": CONSUMER_SECRET,
        "oauth_token":        tokens["oauth_token"],
        "oauth_token_secret": tokens["oauth_token_secret"],
        "user_id": tokens.get("user_id", ""),
    }
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

    print(f"\n✓ Erfolg! Credentials gespeichert: {CREDS_FILE}")
    print(f"  User ID: {creds['user_id']}")
    print("\nFatSecret-Import kann jetzt in der App genutzt werden.")
    print("OAuth 1.0 Tokens laufen nicht ab – einmalige Einrichtung.")


if __name__ == "__main__":
    main()
