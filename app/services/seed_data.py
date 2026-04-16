"""
Seed-Daten: Marcos aktueller Stack (Stand 25.03.2026) + beide Blutbilder.
Wird beim ersten App-Start automatisch geladen wenn die DB leer ist.
"""
from datetime import date
from sqlalchemy.orm import Session

from app.models import (
    Substance, Stack, DoseEvent, Biomarker, BloodPanel, BloodValue,
    DailyLog, MedicalEvent
)


def seed_all(db: Session):
    """Seed-Daten beim ersten Start; Updates immer prüfen."""
    first_run = db.query(Substance).count() == 0
    if first_run:
        _seed_substances(db)
        _seed_biomarkers(db)
        _seed_stack(db)
        _seed_blood_panels(db)
        _seed_garmin_logs(db)
        _seed_medical_events(db)
        db.commit()
        print("Seed-Daten geladen: Stack, Blutbilder, Garmin-Verlauf")
    _update_stack_april_2026(db)


# ─── Substanzen ───────────────────────────────────────────────────────────────

def _seed_substances(db: Session):
    substances = [
        # Steroide
        {"name": "Testosteron Enanthat", "category": "Steroid", "route": "intramuskulaer", "default_unit": "mg", "description": "Basis-Androgen, Anabolismus"},
        {"name": "Drostanolon Enanthat", "category": "Steroid", "route": "intramuskulaer", "default_unit": "mg", "description": "Härte, antiöstrogen, antikatabolisch"},
        {"name": "Trenbolon Enanthat", "category": "Steroid", "route": "intramuskulaer", "default_unit": "mg", "description": "Stärkster Recomp-Wirkstoff, Myostatin-Hemmung"},
        {"name": "Anavar (Oxandrolon)", "category": "Steroid", "route": "oral", "default_unit": "mg", "description": "Lean-Look, Kortisol ↓, oral"},
        # Peptide
        {"name": "HGH (Wachstumshormon)", "category": "Peptid", "route": "subkutan", "default_unit": "IU", "description": "Lipolyse nachts, IGF-1, Muskelschutz"},
        {"name": "Retatrutid", "category": "Peptid", "route": "subkutan", "default_unit": "mg", "description": "GLP-1/GIP/Glucagon Triple-Agonist – Fettabbau"},
        {"name": "BPC-157", "category": "Peptid", "route": "subkutan", "default_unit": "mcg", "description": "Recovery, Verletzungsschutz, Heilung"},
        {"name": "TB-500", "category": "Peptid", "route": "subkutan", "default_unit": "mg", "description": "Muskelreparatur, HRV-Verbesserung"},
        {"name": "AOD-9604", "category": "Peptid", "route": "subkutan", "default_unit": "mcg", "description": "Direkte Lipolyse ohne IGF-1-Erhöhung"},
        # Hormone / Medikamente
        {"name": "Cabergolin", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Prolaktin kontrollieren unter Tren"},
        {"name": "Exemestan", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Aromatase-Hemmer, E2 kontrollieren"},
        {"name": "Telmisartan", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Blutdruck, PPAR-γ, kardioprotektiv"},
        {"name": "Ivabradin", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "HF senken ohne Lipolyse zu dämpfen"},
        {"name": "Metformin", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "AMPK, Insulinsensitivität, HGH-Glukosepuffer"},
        {"name": "Cialis (Tadalafil)", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Vasodilatation, Blutdruck, kardioprotektiv"},
        {"name": "Clenbuterol", "category": "Medikament", "route": "oral", "default_unit": "mcg", "description": "β2-Thermogenese + Lipolyse"},
        {"name": "T3 (Liothyronin)", "category": "Hormon", "route": "oral", "default_unit": "mcg", "description": "Stoffwechsel aktiv halten, Fettabbau"},
        {"name": "Yohimbin", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "α2-Blockade hartnäckiges Fett nüchtern"},
        {"name": "Trazodon", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Tiefschlaf ↑, HGH-Effizienz, Tren-Schlafstörung"},
        {"name": "Ketotifen", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "β2-Upregulation, Clen dauerhaft wirksam"},
        {"name": "5-Amino-1MQ", "category": "Medikament", "route": "oral", "default_unit": "mg", "description": "Mitochondriale Effizienz, NNMT-Hemmung"},
        # Supplemente
        {"name": "NAC (N-Acetylcystein)", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Glutathion, Leberschutz, Antioxidans"},
        {"name": "Kalium", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Clen depletiert Kalium – Ausgleich"},
        {"name": "B-Komplex", "category": "Supplement", "route": "oral", "default_unit": "Portion", "description": "Methylierung, Energie unter T3"},
        {"name": "Omega-3 (EPA/DHA)", "category": "Supplement", "route": "oral", "default_unit": "g", "description": "Kardiovaskulär, Blutviskosität ↓"},
        {"name": "Vitamin D3 + K2", "category": "Supplement", "route": "oral", "default_unit": "IU", "description": "Grundversorgung, Arterien"},
        {"name": "CoQ10", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Mitochondrien, kardioprotektiv"},
        {"name": "Nattokinase", "category": "Supplement", "route": "oral", "default_unit": "FU", "description": "Blutviskosität ↓ bei erhöhtem Hämatokrit"},
        {"name": "Cholin", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Leberfettschutz bei HGH + Tren"},
        {"name": "Vitamin C", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Antioxidans, Kortisol-Modulation"},
        {"name": "Mariendistel (Silymarin)", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Leberschutz"},
        {"name": "Astaxanthin", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Antioxidans, antiinflammatorisch"},
        {"name": "Vitamin B12", "category": "Supplement", "route": "oral", "default_unit": "mcg", "description": "Metformin depletiert B12 langfristig"},
        {"name": "Zink", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Testo-Metabolismus, Aromatase-Modulation"},
        {"name": "Citrus Bergamot", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Lipid-Unterstützung"},
        {"name": "TUDCA", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Gallensäure-Protektion, Leberschutz"},
        {"name": "Essetil Forte", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Phospholipide, Leberzellmembran"},
        {"name": "Taurin", "category": "Supplement", "route": "oral", "default_unit": "g", "description": "Herzrhythmus unter Clen, Krämpfe"},
        {"name": "Magnesium-Komplex", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Schlaf, Krämpfe unter Clen"},
        {"name": "Melatonin", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Schlaf + HGH-Synergist"},
        {"name": "Eisen", "category": "Supplement", "route": "oral", "default_unit": "mg", "description": "Ferritin-Ausgleich nach Aderlass (nach Arzt)"},
    ]
    for s in substances:
        db.add(Substance(**s))
    db.flush()


# ─── Biomarker ────────────────────────────────────────────────────────────────

def _seed_biomarkers(db: Session):
    biomarkers = [
        # Hormone
        {"name": "Testosteron gesamt", "unit": "µg/L", "ref_min": 2.49, "ref_max": 8.36, "category": "Hormone", "aliases": "Testosteron,Testosterone total"},
        {"name": "Testosteron frei", "unit": "ng/dL", "ref_min": None, "ref_max": None, "category": "Hormone", "aliases": "freies Testosteron,Free Testosterone"},
        {"name": "SHBG", "unit": "nmol/L", "ref_min": 18.3, "ref_max": 54.1, "category": "Hormone", "aliases": "Sexualhormon-bindendes Globulin"},
        {"name": "Estradiol", "unit": "ng/L", "ref_min": 11.0, "ref_max": 43.0, "optimal_min": 25.0, "optimal_max": 50.0, "category": "Hormone", "aliases": "E2,Oestradiol"},
        {"name": "Prolaktin", "unit": "µg/L", "ref_min": 4.0, "ref_max": 15.2, "category": "Hormone", "aliases": "Prolactin,PRL"},
        {"name": "LH", "unit": "U/L", "ref_min": 1.7, "ref_max": 8.6, "category": "Hormone", "aliases": "Luteinisierendes Hormon,Luteinizing Hormone"},
        {"name": "FSH", "unit": "U/L", "ref_min": 1.5, "ref_max": 12.4, "category": "Hormone", "aliases": "Follikelstimulierendes Hormon"},
        {"name": "IGF-1", "unit": "µg/L", "ref_min": 78.7, "ref_max": 226.0, "optimal_min": 200.0, "optimal_max": 350.0, "category": "Hormone", "aliases": "Somatomedin C,IGF1"},
        {"name": "TSH", "unit": "mU/L", "ref_min": 0.27, "ref_max": 4.20, "category": "Schilddrüse", "aliases": "Thyreoidea-stimulierendes Hormon"},
        {"name": "fT3", "unit": "ng/L", "ref_min": 2.0, "ref_max": 4.4, "optimal_min": 2.8, "optimal_max": 3.5, "category": "Schilddrüse", "aliases": "freies T3,freies Trijodthyronin,FT3"},
        {"name": "fT4", "unit": "ng/L", "ref_min": 9.2, "ref_max": 16.8, "category": "Schilddrüse", "aliases": "freies Thyroxin,FT4"},
        # Leber
        {"name": "GPT (ALAT)", "unit": "U/L", "ref_min": 10.0, "ref_max": 50.0, "category": "Leber", "aliases": "ALT,ALAT,GPT,Alanin-Aminotransferase"},
        {"name": "GOT (ASAT)", "unit": "U/L", "ref_min": 10.0, "ref_max": 50.0, "category": "Leber", "aliases": "AST,ASAT,GOT,Aspartat-Aminotransferase"},
        {"name": "GGT", "unit": "U/L", "ref_min": 8.0, "ref_max": 61.0, "category": "Leber", "aliases": "Gamma-GT,Gamma-Glutamyltransferase"},
        {"name": "Bilirubin gesamt", "unit": "mg/dL", "ref_min": 0.2, "ref_max": 1.2, "category": "Leber", "aliases": "Gesamtbilirubin"},
        # Blutbild
        {"name": "Hämoglobin", "unit": "g/dL", "ref_min": 13.5, "ref_max": 17.8, "optimal_min": 14.0, "optimal_max": 16.5, "category": "Blutbild", "aliases": "Haemoglobin,Hb"},
        {"name": "Hämatokrit", "unit": "%", "ref_min": 40.0, "ref_max": 53.0, "optimal_min": 42.0, "optimal_max": 50.0, "category": "Blutbild", "aliases": "Haematokrit,Hkt,HKT"},
        {"name": "Erythrozyten", "unit": "T/L", "ref_min": 4.5, "ref_max": 5.9, "category": "Blutbild", "aliases": "Rote Blutkörperchen,RBC"},
        {"name": "Leukozyten", "unit": "G/L", "ref_min": 4.0, "ref_max": 10.0, "category": "Blutbild", "aliases": "WBC,Weiße Blutkörperchen"},
        {"name": "Thrombozyten", "unit": "G/L", "ref_min": 150.0, "ref_max": 400.0, "category": "Blutbild", "aliases": "Platelets,PLT"},
        {"name": "Retikulozyten", "unit": "%", "ref_min": 0.5, "ref_max": 2.0, "category": "Blutbild", "aliases": "Reticulocytes"},
        {"name": "Ferritin", "unit": "µg/L", "ref_min": 30.0, "ref_max": 400.0, "optimal_min": 70.0, "optimal_max": 150.0, "category": "Blutbild", "aliases": "Ferritin,Serum Ferritin"},
        # Niere
        {"name": "Kreatinin", "unit": "mg/dL", "ref_min": 0.67, "ref_max": 1.17, "category": "Niere", "aliases": "Creatinine,Creatinin"},
        {"name": "eGFR (Kreatinin)", "unit": "ml/min", "ref_min": 60.0, "ref_max": None, "category": "Niere", "aliases": "GFR,eGFR,Glomeruläre Filtrationsrate"},
        {"name": "Cystatin C eGFR", "unit": "ml/min", "ref_min": 60.0, "ref_max": None, "category": "Niere", "aliases": "CKD-EPI Cystatin,Cystatin C"},
        # Lipide
        {"name": "LDL", "unit": "mg/dL", "ref_min": None, "ref_max": 115.0, "optimal_min": None, "optimal_max": 100.0, "category": "Lipide", "aliases": "LDL-Cholesterin,LDL-C"},
        {"name": "HDL", "unit": "mg/dL", "ref_min": 45.0, "ref_max": None, "category": "Lipide", "aliases": "HDL-Cholesterin,HDL-C"},
        {"name": "Triglyceride", "unit": "mg/dL", "ref_min": None, "ref_max": 150.0, "category": "Lipide", "aliases": "Triglyzeride,TG"},
        {"name": "Cholesterin gesamt", "unit": "mg/dL", "ref_min": None, "ref_max": 200.0, "category": "Lipide", "aliases": "Gesamtcholesterin,Total Cholesterol"},
        # Stoffwechsel
        {"name": "Glukose", "unit": "mg/dL", "ref_min": 70.0, "ref_max": 100.0, "category": "Stoffwechsel", "aliases": "Glucose,Blutzucker,Nüchternblutzucker"},
        {"name": "HbA1c", "unit": "%", "ref_min": 4.8, "ref_max": 5.9, "category": "Stoffwechsel", "aliases": "HbA1c,Glykiertes Hämoglobin"},
        {"name": "HOMA-Index", "unit": "", "ref_min": None, "ref_max": 1.9, "category": "Stoffwechsel", "aliases": "HOMA,Insulinresistenz"},
        {"name": "Insulin", "unit": "µU/mL", "ref_min": 2.0, "ref_max": 25.0, "category": "Stoffwechsel", "aliases": "Nüchterninsulin"},
        # Pankreas
        {"name": "Lipase", "unit": "U/L", "ref_min": 13.0, "ref_max": 60.0, "category": "Pankreas", "aliases": "Pankreasenzym"},
        # Elektrolyte
        {"name": "Kalium", "unit": "mmol/L", "ref_min": 3.5, "ref_max": 5.1, "category": "Elektrolyte", "aliases": "Kalium serum,K+"},
        {"name": "Natrium", "unit": "mmol/L", "ref_min": 136.0, "ref_max": 145.0, "category": "Elektrolyte", "aliases": "Natrium serum,Na+"},
        # Erweiterte Marker
        {"name": "ApoB", "unit": "mg/dL", "ref_min": None, "ref_max": 100.0, "category": "Lipide", "aliases": "Apolipoprotein B"},
        {"name": "hsCRP", "unit": "mg/L", "ref_min": None, "ref_max": 1.0, "category": "Entzündung", "aliases": "hochsensitives CRP,hs-CRP,CRP"},
        {"name": "Transferrin-Sättigung", "unit": "%", "ref_min": 16.0, "ref_max": 45.0, "category": "Blutbild", "aliases": "TSAT,Transferrinsättigung"},
    ]
    for b in biomarkers:
        db.add(Biomarker(**b))
    db.flush()


# ─── Stack ────────────────────────────────────────────────────────────────────

def _seed_stack(db: Session):
    stack = Stack(
        name="16 Wochen Recomp-Blast",
        goal="8-10% KFA, maximaler Muskelerhalt",
        start_date=date(2026, 2, 23),
        end_date=date(2026, 6, 15),
        status="aktiv",
        notes="16 Wochen Blast. Danach Cruise (Testo 300-400mg, HGH 2-3IU). Montenegro Urlaub Anfang Juli 2026."
    )
    db.add(stack)
    db.flush()

    def get_sub(name):
        return db.query(Substance).filter(Substance.name == name).first()

    start = date(2026, 2, 23)

    dose_events = [
        # Injektionen
        {"substance": "Testosteron Enanthat", "dose_amount": 500, "dose_unit": "mg", "frequency": "2x/Woche", "timing": "250mg Mi abends + 250mg So morgens"},
        {"substance": "Drostanolon Enanthat", "dose_amount": 400, "dose_unit": "mg", "frequency": "2x/Woche", "timing": "200mg Mi abends + 200mg So morgens"},
        {"substance": "Trenbolon Enanthat", "dose_amount": 200, "dose_unit": "mg", "frequency": "2x/Woche", "timing": "100mg Mi abends + 100mg So morgens"},
        {"substance": "HGH (Wachstumshormon)", "dose_amount": 4, "dose_unit": "IU", "frequency": "täglich", "timing": "21-22 Uhr subkutan"},
        {"substance": "Retatrutid", "dose_amount": 2, "dose_unit": "mg", "frequency": "1x/Woche", "timing": "Donnerstag morgens subkutan nüchtern"},
        {"substance": "Cabergolin", "dose_amount": 0.25, "dose_unit": "mg", "frequency": "2x/Woche", "timing": "Mi + So abends (Pin-Tag)"},
        # Nüchtern 07:00
        {"substance": "Telmisartan", "dose_amount": 40, "dose_unit": "mg", "frequency": "täglich", "timing": "07:00 nüchtern"},
        {"substance": "Ivabradin", "dose_amount": 10, "dose_unit": "mg", "frequency": "täglich", "timing": "5mg 07:00 + 5mg 17:00"},
        {"substance": "Yohimbin", "dose_amount": 10, "dose_unit": "mg", "frequency": "täglich", "timing": "07:00 nüchtern", "notes": "→14mg nach Blutbild 01.04 wenn HRV stabil >32ms"},
        {"substance": "Clenbuterol", "dose_amount": 40, "dose_unit": "mcg", "frequency": "täglich", "timing": "07:00 nüchtern", "notes": "Nach Aderlass 26.03 auf 40mcg erhöht"},
        {"substance": "T3 (Liothyronin)", "dose_amount": 37.5, "dose_unit": "mcg", "frequency": "täglich", "timing": "25mcg morgens + 12,5mcg 17-18 Uhr", "notes": "Ab 25.03.2026: 37,5mcg gesamt"},
        # Mit erstem Essen 10-11 Uhr
        {"substance": "Exemestan", "dose_amount": 12.5, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Cialis (Tadalafil)", "dose_amount": 5, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "NAC (N-Acetylcystein)", "dose_amount": 700, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Kalium", "dose_amount": 300, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "B-Komplex", "dose_amount": 1, "dose_unit": "Portion", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Omega-3 (EPA/DHA)", "dose_amount": 3, "dose_unit": "g", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "CoQ10", "dose_amount": 100, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Nattokinase", "dose_amount": 2000, "dose_unit": "FU", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Cholin", "dose_amount": 375, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Vitamin C", "dose_amount": 750, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        {"substance": "Mariendistel (Silymarin)", "dose_amount": 800, "dose_unit": "mg", "frequency": "täglich", "timing": "300mg morgens + 500mg abends"},
        {"substance": "Astaxanthin", "dose_amount": 12, "dose_unit": "mg", "frequency": "täglich", "timing": "10-11 Uhr mit Essen"},
        # 17-18 Uhr
        {"substance": "Metformin", "dose_amount": 1000, "dose_unit": "mg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "Vitamin B12", "dose_amount": 1000, "dose_unit": "mcg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "Zink", "dose_amount": 37.5, "dose_unit": "mg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "Citrus Bergamot", "dose_amount": 500, "dose_unit": "mg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "TUDCA", "dose_amount": 375, "dose_unit": "mg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "Essetil Forte", "dose_amount": 600, "dose_unit": "mg", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        {"substance": "Taurin", "dose_amount": 1, "dose_unit": "g", "frequency": "täglich", "timing": "17-18 Uhr mit Essen"},
        # Vor dem Schlafen
        {"substance": "Magnesium-Komplex", "dose_amount": 300, "dose_unit": "mg", "frequency": "täglich", "timing": "21-22 Uhr"},
        {"substance": "Melatonin", "dose_amount": 1, "dose_unit": "mg", "frequency": "täglich", "timing": "21-22 Uhr"},
        {"substance": "Ketotifen", "dose_amount": 1, "dose_unit": "mg", "frequency": "täglich", "timing": "21-22 Uhr"},
        {"substance": "Trazodon", "dose_amount": 50, "dose_unit": "mg", "frequency": "täglich", "timing": "21-22 Uhr"},
        {"substance": "Eisen", "dose_amount": 0, "dose_unit": "mg", "frequency": "täglich", "timing": "21-22 Uhr", "notes": "Dosis nach Arzt – Ferritin war 122"},
    ]

    for de in dose_events:
        sub = get_sub(de["substance"])
        if sub:
            db.add(DoseEvent(
                stack_id=stack.id,
                substance_id=sub.id,
                dose_amount=de["dose_amount"],
                dose_unit=de["dose_unit"],
                frequency=de["frequency"],
                timing=de["timing"],
                start_date=start,
                notes=de.get("notes"),
            ))
    db.flush()


# ─── Blutbilder ───────────────────────────────────────────────────────────────

def _seed_blood_panels(db: Session):
    stack = db.query(Stack).filter(Stack.name == "16 Wochen Recomp-Blast").first()

    def get_marker(name):
        return db.query(Biomarker).filter(Biomarker.name == name).first()

    # ── Blutbild 1: 30.12.2025 (vor HGH) ─────────────────────────────────────
    panel1 = BloodPanel(
        date=date(2025, 12, 30),
        lab="Unbekannt",
        notes="Vor HGH-Start. Basis-Panel.",
        active_stack_id=None
    )
    db.add(panel1)
    db.flush()

    values1 = [
        ("Hämoglobin", 17.7, "g/dL", 13.5, 17.8),
        ("Hämatokrit", 50.0, "%", 40.0, 53.0),
        ("GPT (ALAT)", 68.0, "U/L", 10.0, 50.0),
        ("Kreatinin", 1.40, "mg/dL", 0.67, 1.17),
        ("eGFR (Kreatinin)", 61.0, "ml/min", 60.0, None),
        ("Cystatin C eGFR", 94.0, "ml/min", 60.0, None),
        ("Estradiol", 51.0, "ng/L", 11.0, 43.0),
        ("Testosteron gesamt", 15.0, "µg/L", 2.49, 8.36),
        ("SHBG", 7.9, "nmol/L", 18.3, 54.1),
        ("IGF-1", 176.0, "µg/L", 78.7, 226.0),
        ("Prolaktin", 16.4, "µg/L", 4.0, 15.2),
        ("fT3", 2.73, "ng/L", 2.0, 4.4),
        ("TSH", 1.71, "mU/L", 0.27, 4.20),
        ("HOMA-Index", 1.0, "", None, 1.9),
        ("Triglyceride", 36.0, "mg/dL", None, 150.0),
        ("LDL", 81.0, "mg/dL", None, 115.0),
        ("HbA1c", 5.3, "%", 4.8, 5.9),
    ]
    for name, val, unit, rmin, rmax in values1:
        marker = get_marker(name)
        if marker:
            db.add(BloodValue(panel_id=panel1.id, biomarker_id=marker.id, value=val, unit=unit, ref_min=rmin, ref_max=rmax))

    # ── Blutbild 2: 02.02.2026 (mit 2IU HGH) ─────────────────────────────────
    panel2 = BloodPanel(
        date=date(2026, 2, 2),
        lab="Unbekannt",
        notes="Mit 2IU HGH. Estradiol erhöht (69 ng/L). HKT an Obergrenze (0,53). Blast noch nicht gestartet.",
        active_stack_id=stack.id if stack else None
    )
    db.add(panel2)
    db.flush()

    values2 = [
        ("Hämoglobin", 18.4, "g/dL", 13.5, 17.8),
        ("Hämatokrit", 53.0, "%", 40.0, 53.0),
        ("GPT (ALAT)", 51.0, "U/L", 10.0, 50.0),
        ("GOT (ASAT)", 27.0, "U/L", 10.0, 50.0),
        ("Estradiol", 69.0, "ng/L", 11.0, 43.0),
        ("IGF-1", 288.0, "µg/L", 78.7, 226.0),
        ("Prolaktin", 5.8, "µg/L", 4.0, 15.2),
        ("fT3", 2.40, "ng/L", 2.0, 4.4),
        ("TSH", 2.12, "mU/L", 0.27, 4.20),
        ("fT4", 16.2, "ng/L", 9.2, 16.8),
        ("HOMA-Index", 1.3, "", None, 1.9),
        ("Glukose", 94.0, "mg/dL", 70.0, 100.0),
        ("Kalium", 5.1, "mmol/L", 3.5, 5.1),
        ("Ferritin", 122.0, "µg/L", 30.0, 400.0),
        ("Triglyceride", 66.0, "mg/dL", None, 150.0),
        ("HDL", 46.0, "mg/dL", 45.0, None),
        ("LDL", 73.0, "mg/dL", None, 115.0),
        ("HbA1c", 5.3, "%", 4.8, 5.9),
    ]
    for name, val, unit, rmin, rmax in values2:
        marker = get_marker(name)
        if marker:
            db.add(BloodValue(panel_id=panel2.id, biomarker_id=marker.id, value=val, unit=unit, ref_min=rmin, ref_max=rmax))

    db.flush()


# ─── Garmin-Verlauf ───────────────────────────────────────────────────────────

def _seed_garmin_logs(db: Session):
    logs = [
        {"date": date(2026, 3, 15), "hrv": 23, "heart_rate_night": 78, "sleep_score": 58, "weight": 74.0, "notes": "Baseline"},
        {"date": date(2026, 3, 16), "hrv": 24, "heart_rate_night": 70, "sleep_score": 78, "deep_sleep_min": 41, "body_battery": 39, "weight": 72.4, "night_sweat": "ja"},
        {"date": date(2026, 3, 17), "hrv": 24, "heart_rate_night": 66, "sleep_score": 57, "deep_sleep_min": 34, "body_battery": 44, "weight": 72.6, "night_sweat": "weniger"},
        {"date": date(2026, 3, 18), "hrv": 26, "heart_rate_night": 66, "sleep_score": 57, "deep_sleep_min": 41, "body_battery": 39, "weight": 72.5, "night_sweat": "nein"},
        {"date": date(2026, 3, 20), "hrv": 27, "heart_rate_night": 64, "sleep_score": 74, "deep_sleep_min": 53, "body_battery": 40, "weight": 72.6, "night_sweat": "ja", "notes": "Clen auf 30mcg"},
        {"date": date(2026, 3, 21), "hrv": 32, "heart_rate_night": 66, "sleep_score": 68, "deep_sleep_min": 39, "body_battery": 45, "weight": 72.5, "night_sweat": "ja"},
        {"date": date(2026, 3, 22), "hrv": 32, "heart_rate_night": 61, "sleep_score": 74, "deep_sleep_min": 32, "body_battery": 61, "weight": 72.5, "night_sweat": "ja"},
        {"date": date(2026, 3, 24), "hrv": 32, "heart_rate_night": 64, "weight": 71.4, "night_sweat": "ja", "notes": "T3 auf 37,5mcg gestern"},
    ]
    for log_data in logs:
        log = DailyLog(source="garmin", **log_data)
        db.add(log)
    db.flush()


# ─── Medizinische Ereignisse ──────────────────────────────────────────────────

def _seed_medical_events(db: Session):
    db.add(MedicalEvent(
        date=date(2026, 3, 30),
        event_type="Aderlass",
        amount_ml=450,
        location="Blutspendezentrum Bremen",
        notes="Aderlass 1 von geplant 2. Hämatokrit war 0,53 – Ziel: <0,50. Blut nicht für Transfusion verwendbar (Stack). Danach Clen auf 40mcg erhöht."
    ))
    db.flush()


# ─── Stack-Update 02.04.2026 ──────────────────────────────────────────────────

def _close_active_dose_events(db: Session, stack_id: int, substance_name: str, end_date):
    """Setzt end_date aller offenen DoseEvents für eine Substanz im Stack."""
    sub = db.query(Substance).filter(Substance.name == substance_name).first()
    if not sub:
        return
    events = (
        db.query(DoseEvent)
        .filter(DoseEvent.stack_id == stack_id, DoseEvent.substance_id == sub.id, DoseEvent.end_date == None)
        .all()
    )
    for ev in events:
        ev.end_date = end_date


def _update_stack_april_2026(db: Session):
    """
    Stack-Änderungen ab 02.04.2026 nach Blutbild 01.04.2026.
    Sentinel: DoseEvent.change_reason == 'Stack-Update 02.04.2026'
    """
    from app.models import DoseEvent as DE
    if db.query(DE).filter(DE.change_reason == "Stack-Update 02.04.2026").first():
        return  # Bereits angewendet

    stack = db.query(Stack).filter(Stack.name == "16 Wochen Recomp-Blast").first()
    if not stack:
        return

    upd = date(2026, 4, 2)
    end_old = date(2026, 4, 1)

    def sub(name):
        return db.query(Substance).filter(Substance.name == name).first()

    def add(substance_name, dose_amount, dose_unit, frequency, timing, notes=None):
        s = sub(substance_name)
        if s:
            db.add(DoseEvent(
                stack_id=stack.id, substance_id=s.id,
                dose_amount=dose_amount, dose_unit=dose_unit,
                frequency=frequency, timing=timing,
                start_date=upd, change_reason="Stack-Update 02.04.2026",
                notes=notes,
            ))

    # 1. Cabergolin: 2x/Woche → 1x/Woche Mittwoch
    _close_active_dose_events(db, stack.id, "Cabergolin", end_old)
    add("Cabergolin", 0.25, "mg", "1x/Woche",
        "Mittwoch abends (Pin-Tag)",
        "Prolaktin gecrasht auf 0.9 µg/L – reduziert")

    # 2. Yohimbin: 10mg → 15mg
    _close_active_dose_events(db, stack.id, "Yohimbin", end_old)
    add("Yohimbin", 15, "mg", "täglich",
        "07:00 nüchtern")

    # 3. B-Komplex: raus
    _close_active_dose_events(db, stack.id, "B-Komplex", end_old)

    # 4. Vitamin C: raus
    _close_active_dose_events(db, stack.id, "Vitamin C", end_old)

    # 5. NAC: 800mg 2x täglich (morgens + abends)
    _close_active_dose_events(db, stack.id, "NAC (N-Acetylcystein)", end_old)
    add("NAC (N-Acetylcystein)", 800, "mg", "2x täglich",
        "10-11 Uhr mit Essen (1. Dosis)",
        "GPT 105 – Leberschutz intensiviert. 2. Dosis 17-18 Uhr.")
    s_nac = sub("NAC (N-Acetylcystein)")
    if s_nac:
        db.add(DoseEvent(
            stack_id=stack.id, substance_id=s_nac.id,
            dose_amount=800, dose_unit="mg", frequency="2x täglich",
            timing="17-18 Uhr mit Mahlzeit (2. Dosis)",
            start_date=upd, change_reason="Stack-Update 02.04.2026",
            notes="2. Tagesdosis Leberschutz",
        ))

    # 6. Omega-3: 2x2 Kapseln/Tag Bodylab Extreme
    _close_active_dose_events(db, stack.id, "Omega-3 (EPA/DHA)", end_old)
    add("Omega-3 (EPA/DHA)", 2, "Kapseln", "2x täglich",
        "10-11 Uhr: 2 Kapseln Bodylab Extreme (1. Dosis)",
        "HDL 33 – therapeutische Dosis. 2. Dosis 17-18 Uhr.")
    s_o3 = sub("Omega-3 (EPA/DHA)")
    if s_o3:
        db.add(DoseEvent(
            stack_id=stack.id, substance_id=s_o3.id,
            dose_amount=2, dose_unit="Kapseln", frequency="2x täglich",
            timing="17-18 Uhr: 2 Kapseln Bodylab Extreme (2. Dosis)",
            start_date=upd, change_reason="Stack-Update 02.04.2026",
            notes="2. Tagesdosis für HDL",
        ))

    # 7. Essetil Forte: 600mg 2x täglich (morgens + abends)
    _close_active_dose_events(db, stack.id, "Essetil Forte", end_old)
    add("Essetil Forte", 600, "mg", "2x täglich",
        "10-11 Uhr mit Essen (1. Dosis)",
        "GPT 105 – Phospholipide erhöht")
    s_es = sub("Essetil Forte")
    if s_es:
        db.add(DoseEvent(
            stack_id=stack.id, substance_id=s_es.id,
            dose_amount=600, dose_unit="mg", frequency="2x täglich",
            timing="17-18 Uhr mit Mahlzeit (2. Dosis)",
            start_date=upd, change_reason="Stack-Update 02.04.2026",
            notes="2. Tagesdosis Essetil Forte",
        ))

    # 8. Exemestan: 10 Tage täglich 25mg, dann alternierend 12,5/25mg
    _close_active_dose_events(db, stack.id, "Exemestan", end_old)
    add("Exemestan", 25, "mg", "täglich (10 Tage), dann alternierend",
        "10-11 Uhr mit Essen",
        "E2 war 99 ng/L. 02.04–11.04: täglich 25mg. Ab 12.04: alternierend 12,5mg / 25mg je Tag.")

    db.commit()
    print("Stack-Update 02.04.2026 angewendet")
