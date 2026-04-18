"""
Einheitliche Zielgruppen-Schätzung für Gerätekatalog (gym80 / Matrix / eGym).

Wird von API-Suche, Supabase-Sync und Hilfsskripten genutzt — eine Logik,
damit lokal und online dieselbe Einordnung entsteht.
"""

from __future__ import annotations


def normalize_catalog_brand_key(brand: str) -> str:
    b = (brand or "").strip().lower()
    if "matrix" in b:
        return "matrix"
    if "egym" in b:
        return "egym"
    return "gym80"


def infer_target(text: str) -> str:
    """
    Zielgruppe (Brust, Rücken, Core, …) aus kombiniertem Freitext:
    Modellname, muscle_groups, Kategorie.
    """
    v = (text or "").lower()

    # Core / Bauch früh (vor generischen „press“-Treffern)
    if any(
        x in v
        for x in (
            "klappsitz",
            "abdominal bench",
            "bauchbank",
            "hyperextension",
            "hyperext",
            "rückentrainer",
            "rueckentrainer",
            "back extension",
            "roman chair",
            "crunch",
            "sit-up",
            "sit up",
            "bauch",
            "abdominal",
            "torso rotation",
            "rotation core",
        )
    ):
        return "Core"

    if any(x in v for x in ("hip thrust", "glute", "gesäß", "gess", " po ", "abdukt")):
        return "Glutes"

    if any(
        x in v
        for x in (
            "lat ",
            "lat.",
            " rowing",
            "row ",
            "rücken",
            "ruecken",
            "ruder",
            "pulldown",
            "pull-down",
            "latziehen",
            "latissimus",
            "reverse butterfly",
        )
    ):
        return "Rücken"

    if any(x in v for x in ("biceps", "triceps", "bizeps", "trizeps", "curl", "curls")):
        return "Arme"

    if any(x in v for x in ("shoulder", "schulter", "delt", "seitheb")):
        return "Schulter"

    if any(
        x in v
        for x in (
            "leg ",
            "leg-",
            "quad",
            "ham",
            "bein",
            "squat",
            "knie",
            "wade",
            "calf",
            "hack squat",
        )
    ):
        return "Beine"

    if any(x in v for x in ("chest", "brust", "fly", "flye", "pec ", "crossover", "butterfly")):
        return "Brust"

    if "press" in v or "bench" in v:
        if not any(x in v for x in ("shoulder", "schulter", "lat", "leg", "bein", "knie")):
            return "Brust"

    if any(
        x in v
        for x in (
            "cardio",
            "bike",
            "treadmill",
            "elliptical",
            "climb",
            "laufband",
            "ergometer",
            "crosstrainer",
            "stepper",
            "rowing machine",
            "rudergerät",
            "fahrrad",
        )
    ):
        return "Cardio"

    # Kein Treffer: konservativ Core (Sonderbänke, Zubehör) statt willkürlich „Brust“
    return "Core"


# Kanonischer Filter-Slug (UI/API); session_type entspricht infer_stype (push/pull/legs/cardio/free).
TARGET_DISPLAY_TO_KEY: dict[str, str] = {
    "Brust": "chest",
    "Rücken": "back",
    "Beine": "legs",
    "Core": "core",
    "Glutes": "glutes",
    "Arme": "arms",
    "Schulter": "shoulders",
    "Cardio": "cardio",
}


def target_to_key(target_display: str) -> str:
    t = (target_display or "").strip()
    return TARGET_DISPLAY_TO_KEY.get(t, "core")


def infer_stype(target_name: str, *, is_matrix_cardio_row: bool = False) -> str:
    if is_matrix_cardio_row:
        return "cardio"
    tt = (
        (target_name or "")
        .strip()
        .lower()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )
    if tt in ("rucken", "ruecken", "rücken") or tt.startswith("ruck"):
        return "pull"
    if tt in ("beine", "glutes", "legs"):
        return "legs"
    if tt == "cardio":
        return "cardio"
    if tt == "core":
        return "free"
    return "push"
