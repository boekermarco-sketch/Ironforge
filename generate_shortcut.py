"""
Generates ironforge-health-sync.shortcut
Per Mail ans iPhone schicken → antippen → direkt in Kurzbefehle importiert.

Prerequisite iOS: Einstellungen > Kurzbefehle > Nicht vertrauenswürdigen Kurzbefehlen erlauben = AN
"""
import plistlib
import uuid
from pathlib import Path

SUPABASE_URL = "https://dbamakgjtrgqplufwlca.supabase.co/rest/v1/apple_health_daily"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiYW1ha2dqdHJncXBsdWZ3bGNhIiwicm9sZSI6ImFub24iL"
    "CJpYXQiOjE3NzYwODY0MzMsImV4cCI6MjA5MTY2MjQzM30"
    ".nXRtfxvgqg0Ccgo2FRtFYGrBjx-voNfQOpDCAzK_EME"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gen():
    return str(uuid.uuid4()).upper()


def var_ref(output_name: str, output_uuid: str) -> dict:
    """Magic variable – reference to a previous action output."""
    return {
        "Value": {
            "Type": "ActionOutput",
            "OutputName": output_name,
            "OutputUUID": output_uuid,
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def text_var(output_name: str, output_uuid: str) -> dict:
    """Variable embedded as token in a WFTextTokenString (used in dict values)."""
    return {
        "Value": {
            "attachmentsByRange": {
                "{0, 1}": {
                    "Type": "ActionOutput",
                    "OutputName": output_name,
                    "OutputUUID": output_uuid,
                }
            },
            "string": "\ufffc",  # U+FFFC OBJECT REPLACEMENT CHARACTER
        },
        "WFSerializationType": "WFTextTokenString",
    }


def text_lit(s: str) -> dict:
    return {
        "Value": {"attachmentsByRange": {}, "string": s},
        "WFSerializationType": "WFTextTokenString",
    }


def dict_field(key: str, value_token: dict) -> dict:
    return {
        "WFItemType": 0,  # Text
        "WFKey": text_lit(key),
        "WFValue": value_token,
    }


def wf_dict(items: list) -> dict:
    return {
        "Value": {"WFDictionaryFieldValueItems": items},
        "WFSerializationType": "WFDictionaryFieldValue",
    }


# ---------------------------------------------------------------------------
# Action builders
# ---------------------------------------------------------------------------

def action_current_date() -> tuple[dict, str]:
    u = gen()
    return (
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.date",
            "WFWorkflowActionParameters": {
                "WFDateActionMode": "Current Date",
                "UUID": u,
                "CustomOutputName": "Datum",
            },
        },
        u,
    )


def action_find_health(health_type: str, output_name: str, days: int = 3, limit: int = 1) -> tuple[dict, str]:
    u = gen()
    return (
        {
            # iOS 15+ correct identifier (was health.quantity.find in older iOS)
            "WFWorkflowActionIdentifier": "is.workflow.actions.filter.health.quantity",
            "WFWorkflowActionParameters": {
                # camelCase HKQuantityTypeIdentifier values (without HK prefix)
                "WFContentItemClass": "WFHealthQuantitySampleContentItem",
                "WFContentItemFilter": {
                    "Value": {
                        "WFActionParameterFilterPrefix": 1,
                        "WFActionParameterFilterProperties": [
                            {
                                "Property": "WFHealthQuantityType",
                                "Relation": "is",
                                "OperandOne": health_type,
                            }
                        ],
                        "WFActionParameterFilterBoundedDate": False,
                        "WFActionParameterFilterDate": {
                            "WFRelativeDateBehavior": "Before",
                            "WFRelativeDateOffset": days,
                            "WFRelativeDateUnit": "Days",
                        },
                    },
                    "WFSerializationType": "WFContentPredicateTableTemplate",
                },
                "WFContentItemSortProperty": "Date",
                "WFContentItemSortOrder": "Newest First",
                "WFContentItemLimitEnabled": True,
                "WFContentItemLimit": limit,
                "UUID": u,
                "CustomOutputName": output_name,
            },
        },
        u,
    )


def action_health_detail(input_name: str, input_uuid: str, output_name: str) -> tuple[dict, str]:
    u = gen()
    return (
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getdetailofhealthsample",
            "WFWorkflowActionParameters": {
                "WFHealthDetailType": "Quantity",   # "Quantity" = numeric value field
                "WFInput": var_ref(input_name, input_uuid),
                "UUID": u,
                "CustomOutputName": output_name,
            },
        },
        u,
    )


# ---------------------------------------------------------------------------
# Build actions list
# ---------------------------------------------------------------------------

actions = []

# A1 – Aktuelles Datum
a, date_uuid = action_current_date()
actions.append(a)

# HKQuantityTypeIdentifier camelCase strings (no HK prefix, as used in Shortcuts plist)
# A2+A3 – Kalorien
a, cal_s = action_find_health("dietaryEnergyConsumed", "Kalorien Proben")
actions.append(a)
a, cal_v = action_health_detail("Kalorien Proben", cal_s, "Kalorien")
actions.append(a)

# A4 – Protein
a, prot_s = action_find_health("dietaryProtein", "Protein Proben")
actions.append(a)
a, prot_v = action_health_detail("Protein Proben", prot_s, "Protein")
actions.append(a)

# A5 – Kohlenhydrate
a, carb_s = action_find_health("dietaryCarbohydrates", "Carbs Proben")
actions.append(a)
a, carb_v = action_health_detail("Carbs Proben", carb_s, "Carbs")
actions.append(a)

# A6 – Fett
a, fat_s = action_find_health("dietaryFatTotal", "Fett Proben")
actions.append(a)
a, fat_v = action_health_detail("Fett Proben", fat_s, "Fett")
actions.append(a)

# A7 – Körpermasse
a, mass_s = action_find_health("bodyMass", "Masse Proben")
actions.append(a)
a, mass_v = action_health_detail("Masse Proben", mass_s, "Koerpermasse")
actions.append(a)

# A8 – Ruhepuls
a, hr_s = action_find_health("restingHeartRate", "HR Proben")
actions.append(a)
a, hr_v = action_health_detail("HR Proben", hr_s, "Ruhepuls")
actions.append(a)

# A9 – Schritte (nur heute)
a, steps_s = action_find_health("stepCount", "Schritte Proben", days=1)
actions.append(a)
a, steps_v = action_health_detail("Schritte Proben", steps_s, "Schritte")
actions.append(a)

# A10 – Wörterbuch
dict_uuid = gen()
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.dictionary",
        "WFWorkflowActionParameters": {
            "WFItems": wf_dict(
                [
                    dict_field("date",         text_var("Datum",        date_uuid)),
                    dict_field("calories",     text_var("Kalorien",     cal_v)),
                    dict_field("protein_g",    text_var("Protein",      prot_v)),
                    dict_field("carbs_g",      text_var("Carbs",        carb_v)),
                    dict_field("fat_g",        text_var("Fett",         fat_v)),
                    dict_field("body_mass_kg", text_var("Koerpermasse", mass_v)),
                    dict_field("resting_hr",   text_var("Ruhepuls",     hr_v)),
                    dict_field("steps",        text_var("Schritte",     steps_v)),
                ]
            ),
            "UUID": dict_uuid,
            "CustomOutputName": "Daten",
        },
    }
)

# A11 – HTTP POST → Supabase
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
        "WFWorkflowActionParameters": {
            "WFURL": SUPABASE_URL,
            "WFHTTPMethod": "POST",
            "WFHTTPBodyType": "JSON",
            "WFHTTPInputBody": var_ref("Daten", dict_uuid),
            "WFHTTPHeaders": wf_dict(
                [
                    dict_field("apikey",        text_lit(SUPABASE_KEY)),
                    dict_field("Authorization", text_lit(f"Bearer {SUPABASE_KEY}")),
                    dict_field("Prefer",        text_lit("resolution=merge-duplicates")),
                    dict_field("Content-Type",  text_lit("application/json")),
                ]
            ),
        },
    }
)

# ---------------------------------------------------------------------------
# Assemble & write
# ---------------------------------------------------------------------------

shortcut = {
    "WFWorkflowClientVersion": "1190.0.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowActions": actions,
    "WFWorkflowImportQuestions": [],
    "WFWorkflowInputContentItemClasses": [],
    "WFWorkflowTypes": [],
    "WFWorkflowHasShortcutInputVariables": False,
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 4278238207,   # orange-ish
        "WFWorkflowIconGlyphNumber": 59511,
    },
    "WFWorkflowNoInputBehavior": {
        "Name": "WFWorkflowNoInputBehaviorAskForInput",
        "Parameters": {},
    },
}

out = Path(__file__).parent / "ironforge-health-sync.shortcut"
with open(out, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_XML)

print(f"OK  Shortcut-Datei erstellt: {out}")
print()
print("Naechste Schritte:")
print("  1. ironforge-health-sync.shortcut per Mail an dich selbst schicken")
print("  2. iPhone: Einstellungen > Kurzbefehle > 'Nicht vertrauenswuerdige erlauben' = AN")
print("  3. Mail auf iPhone oeffnen > Anhang antippen > 'Kurzbefehl hinzufuegen'")
print("  4. Automation auf taeglich 23:30 Uhr einrichten (1x, 1 Min)")
