from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.database import Base


class SubstanceCategory(str, enum.Enum):
    steroid = "Steroid"
    peptid = "Peptid"
    medikament = "Medikament"
    supplement = "Supplement"
    hormon = "Hormon"
    sonstiges = "Sonstiges"


class RouteType(str, enum.Enum):
    oral = "oral"
    subkutan = "subkutan"
    intramuskulaer = "intramuskulaer"
    sonstiges = "sonstiges"


class StackStatus(str, enum.Enum):
    aktiv = "aktiv"
    abgeschlossen = "abgeschlossen"
    geplant = "geplant"
    cruise = "cruise"


class EventType(str, enum.Enum):
    aderlass = "Aderlass"
    blutspende = "Blutspende"
    arzttermin = "Arzttermin"
    sonstiges = "Sonstiges"


class JournalType(str, enum.Enum):
    fortschrittsfoto = "Fortschrittsfoto"
    blutbild = "Blutbild"
    garmin = "Garmin"
    allgemein = "Allgemein"
    checkin = "Check-in"


# ─── Substanzen ───────────────────────────────────────────────────────────────

class Substance(Base):
    __tablename__ = "substances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    route = Column(String(50), default="oral")
    default_unit = Column(String(20), default="mg")
    description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dose_events = relationship("DoseEvent", back_populates="substance")


# ─── Stacks ───────────────────────────────────────────────────────────────────

class Stack(Base):
    __tablename__ = "stacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    goal = Column(String(200))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String(50), default="aktiv")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    dose_events = relationship("DoseEvent", back_populates="stack")
    blood_panels = relationship("BloodPanel", back_populates="active_stack")


class DoseEvent(Base):
    """Historisierte Dosierungsänderung - nie überschreiben, nur neue Einträge."""
    __tablename__ = "dose_events"

    id = Column(Integer, primary_key=True, index=True)
    stack_id = Column(Integer, ForeignKey("stacks.id"))
    substance_id = Column(Integer, ForeignKey("substances.id"), nullable=False)
    dose_amount = Column(Float, nullable=False)
    dose_unit = Column(String(20), default="mg")
    frequency = Column(String(100))   # z.B. "2x/Woche", "täglich", "EOD"
    timing = Column(String(200))      # z.B. "07:00 nüchtern", "Mi+So abends"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)           # NULL = noch aktiv
    change_reason = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    stack = relationship("Stack", back_populates="dose_events")
    substance = relationship("Substance", back_populates="dose_events")


# ─── Blutbilder ───────────────────────────────────────────────────────────────

class Biomarker(Base):
    """Stammdaten aller Labormarker."""
    __tablename__ = "biomarkers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    unit = Column(String(50))
    ref_min = Column(Float)
    ref_max = Column(Float)
    optimal_min = Column(Float)   # Leistungsoptimierter Bereich (nicht nur "normal")
    optimal_max = Column(Float)
    category = Column(String(100))  # Hormone, Leber, Blutbild, Niere, Lipide, etc.
    aliases = Column(Text)          # Kommagetrennte alternative Namen für PDF-Parser

    values = relationship("BloodValue", back_populates="biomarker")


class BloodPanel(Base):
    """Eine einzelne Blutabnahme / Laborauswertung."""
    __tablename__ = "blood_panels"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    lab = Column(String(200))
    notes = Column(Text)
    active_stack_id = Column(Integer, ForeignKey("stacks.id"))
    source_file = Column(String(500))  # Original-PDF-Dateiname
    created_at = Column(DateTime, default=datetime.utcnow)

    active_stack = relationship("Stack", back_populates="blood_panels")
    values = relationship("BloodValue", back_populates="panel", cascade="all, delete-orphan")


class BloodValue(Base):
    """Einzelner Markerwert in einem Blutbild."""
    __tablename__ = "blood_values"

    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("blood_panels.id"), nullable=False)
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    ref_min = Column(Float)   # Referenz des Labors (kann abweichen)
    ref_max = Column(Float)
    notes = Column(String(500))

    panel = relationship("BloodPanel", back_populates="values")
    biomarker = relationship("Biomarker", back_populates="values")


# ─── Tages-Logs ───────────────────────────────────────────────────────────────

class DailyLog(Base):
    """Tägliche Messungen – manuell, Garmin oder Withings."""
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    source = Column(String(50), default="manuell")  # manuell / garmin / withings / gemischt

    # Garmin
    hrv = Column(Float)               # ms
    heart_rate_night = Column(Float)  # bpm
    sleep_score = Column(Integer)     # 0-100
    deep_sleep_min = Column(Integer)  # Minuten
    rem_sleep_min = Column(Integer)
    total_sleep_min = Column(Integer)
    body_battery = Column(Integer)    # 0-100
    breath_rate = Column(Float)       # brpm
    steps = Column(Integer)
    vo2max = Column(Float)
    stress_avg = Column(Integer)

    # Withings
    weight = Column(Float)            # kg
    body_fat = Column(Float)          # %
    muscle_mass = Column(Float)       # kg
    bmi = Column(Float)
    resting_pulse = Column(Integer)

    # MyFitnessPal / Ernährung
    calories = Column(Integer)
    protein = Column(Float)           # g
    carbs = Column(Float)
    fat = Column(Float)

    # Subjektiv (1-10 Skala wenn nicht anders)
    energy_level = Column(Integer)
    libido = Column(Integer)
    mood = Column(Integer)
    training_feel = Column(Integer)
    water_retention = Column(Integer) # 1-5
    acne = Column(Integer)            # 1-5
    night_sweat = Column(String(20))  # ja / nein / weniger
    training_sessions = Column(Integer)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Medizinische Ereignisse ──────────────────────────────────────────────────

class MedicalEvent(Base):
    """Aderlass, Blutspende, Arzttermin etc."""
    __tablename__ = "medical_events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    event_type = Column(String(50), nullable=False)  # Aderlass / Blutspende / Arzttermin
    amount_ml = Column(Integer)          # bei Aderlass/Blutspende
    location = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Konsultations-Journal ────────────────────────────────────────────────────

class JournalEntry(Base):
    """
    Chronologisches Journal für KI-Konsultationen, Fotos und Analysen.
    Alles was bisher in Claude-Chats besprochen wurde, landet hier dauerhaft.
    """
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    time = Column(String(10))            # HH:MM
    title = Column(String(500), nullable=False)
    entry_type = Column(String(50), default="Allgemein")  # Fortschrittsfoto / Blutbild / Garmin / Check-in / Allgemein
    image_path = Column(String(1000))    # relativer Pfad zum Bild
    analysis_text = Column(Text)         # KI-Analyse oder manuelle Notiz
    tags = Column(String(500))           # kommagetrennte Tags
    weight_at_time = Column(Float)       # optionale Schnappschuss-Daten
    body_fat_at_time = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
