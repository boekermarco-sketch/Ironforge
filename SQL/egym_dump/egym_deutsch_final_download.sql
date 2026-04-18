CREATE TABLE IF NOT EXISTS egym_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    series VARCHAR(100),
    code VARCHAR(20),
    model VARCHAR(255) NOT NULL,
    product_url TEXT,
    image_url TEXT,
    muscle_groups TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS egym_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    series VARCHAR(100),
    program_name VARCHAR(255) NOT NULL,
    program_url TEXT,
    training_goals TEXT,
    training_methods TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS egym_modes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    series VARCHAR(100),
    mode_name VARCHAR(255) NOT NULL,
    mode_url TEXT,
    description TEXT,
    notes TEXT
);

INSERT INTO egym_devices (category, series, code, model, product_url, image_url, muscle_groups, notes) VALUES
('smartstrength', 'EGYM Smart Strength', 'M1', 'BEINSTRECKER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M2', 'BAUCHTRAINER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Bauchmuskeln', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M3', 'RÜCKENSTRECKER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'unterer Rücken, Rückenstrecker', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M4', 'BEINBEUGER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Hamstrings', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M5', 'BRUSTPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Brust, Trizeps, vordere Schulter', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M6', 'RUDERZUG', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Rückenmitte, Latissimus, Bizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M7', 'LATZUG', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Latissimus, oberer Rücken, Bizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M8', 'GLUTEUS', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Gesäß', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M9', 'BEINPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps, Gesäß, Hamstrings', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M10', 'ABDUKTORENMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Abduktoren, Gesäß', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M11', 'ADDUKTORENMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Adduktoren', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M12', 'RUMPFROTATION', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Core, schräge Bauchmuskeln', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M13', 'BUTTERFLY', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Brust, vordere Schulter', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M14', 'REVERSE BUTTERFLY', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'hintere Schulter, oberer Rücken', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M15', 'BIZEPSMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Bizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M16', 'WADENPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Waden', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M17', 'SCHULTERPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Schultern, Trizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M18', 'TRIZEPSMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Trizeps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M19', 'HIP THRUST', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Gesäß, hintere Kette', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M20', 'KNIEBEUGE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps, Gesäß, Hamstrings, Core', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'https://de.egym.com/de/workouts/smartstrength', 'SMART STRENGTH ZIRKEL', 'https://de.egym.com/de/workouts/smartstrength', 'https://de.egym.com/sites/default/files/egym-brand/WYSIWYG/WYSIWYG_Smart-Strength-Circuit_desktop_X2.png', 'Ganzkörper', 'Geführter 8-Geräte-Zirkel'),
('smartstrength', 'EGYM Pro', 'PRO', 'EGYM PRO', 'https://de.egym.com/de/workouts/smartstrength/pro', 'https://de.egym.com/sites/default/files/egym-brand/WYSIWYG/WYSIWIG_EGYM_Pro_machines.jpg', 'Ganzkörper', 'Open Mode / freie Trainingsfläche'),
('smartstrength', 'EGYM Smart Flex', 'SMARTFLEX', 'SMART FLEX', 'https://de.egym.com/de/workouts/smartflex', 'https://de.egym.com/sites/default/files/styles/max_width_750px/public/egym-brand/Icon%20Grid%20Right%20Image%20left/ImageLeftIconRight_SmartFlex_NEW_EN_Mobile_X2_0.jpg?itok=LHrgn9ES', 'Mobilität, Beweglichkeit', 'Mobility-System');

INSERT INTO egym_programs (category, series, program_name, program_url, training_goals, training_methods, notes) VALUES
('smartstrength', 'EGYM Smart Strength', 'GEWICHTSREDUKTION', 'https://de.egym.com/de/workouts/smartstrength', 'Gewichtsreduktion', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'MUSKELAUFBAU', 'https://de.egym.com/de/workouts/smartstrength', 'Muskelaufbau', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'ATHLETIK', 'https://de.egym.com/de/workouts/smartstrength', 'Athletik, Performance', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'ALLGEMEINE FITNESS', 'https://de.egym.com/de/workouts/smartstrength', 'Allgemeine Fitness', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'REHAB FIT', 'https://de.egym.com/de/workouts/smartstrength', 'Rehabilitation, Wiedereinstieg', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'BODY TONING', 'https://de.egym.com/de/workouts/smartstrength', 'Straffung, Formung', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'METABOLIC FIT', 'https://de.egym.com/de/workouts/smartstrength', 'Stoffwechsel, Kalorienverbrauch', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm'),
('smartstrength', 'EGYM Smart Strength', 'IMMUNITY BOOST', 'https://de.egym.com/de/workouts/smartstrength', 'Allgemeines Wohlbefinden', 'Regular, Negative, Adaptive, Explonic', 'Smart Strength Programm');

INSERT INTO egym_modes (category, series, mode_name, mode_url, description, notes) VALUES
('smartstrength', 'EGYM Smart Strength', 'REGULAR', 'https://us.egym.com/en-us/blog/egym-training-method-regular', 'Klassische konzentrische und exzentrische Wiederholungen mit geführter Laststeuerung.', 'Trainingsmethode'),
('smartstrength', 'EGYM Smart Strength', 'NEGATIVE', 'https://de.egym.com/de/workouts/smartstrength', 'Stärkerer Fokus auf exzentrische Belastung als auf konzentrische Belastung.', 'Trainingsmethode'),
('smartstrength', 'EGYM Smart Strength', 'ADAPTIVE', 'https://de.egym.com/de/workouts/smartstrength', 'Der Widerstand passt sich während der Bewegung dynamisch an die Leistung an.', 'Trainingsmethode'),
('smartstrength', 'EGYM Smart Strength', 'EXPLONIC', 'https://de.egym.com/de/workouts/smartstrength', 'Explosiver konzentrischer Fokus mit kontrollierter exzentrischer Phase.', 'Trainingsmethode'),
('smartstrength', 'EGYM Pro', 'OPEN MODE', 'https://knowledge.egym.com/de/smart-strength/-en--smart-strength-open-mode-onboarding-guide', 'Freier Trainingsmodus mit unabhängiger Gerätenutzung außerhalb des geführten Zirkelablaufs.', 'Betriebsmodus'),
('smartstrength', 'EGYM Smart Strength', 'GEFÜHRTER ZIRKEL', 'https://uk.egym.com/en-gb/workouts/smartstrength/circuit', 'Strukturierter 8-Geräte-Zirkel mit automatischer Einstellung und geführter Progression.', 'Betriebsmodus');