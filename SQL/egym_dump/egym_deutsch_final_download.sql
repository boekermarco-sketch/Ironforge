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
('smartstrength', 'EGYM Smart Strength', 'M1', 'BEINSTRECKER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps, quadriceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M2', 'BAUCHTRAINER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Bauchmuskeln, abs, abdominals', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M3', 'RÜCKENSTRECKER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'unterer Rücken, lower back, Rückenstrecker, erector spinae', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M4', 'BEINBEUGER', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Hamstrings, Beinbeuger', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M5', 'BRUSTPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Brust, chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M6', 'RUDERZUG', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/sites/default/files/egym-brand/WYSIWYG/WYSIWIG_EGYM_Pro_machines.jpg', 'Rückenmitte, mid back, Latissimus, lats, Bizeps, biceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M7', 'LATZUG', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Latissimus, lats, oberer Rücken, upper back, Bizeps, biceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M9', 'BEINPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps, quadriceps, Gesäß, glutes, Hamstrings, Beinbeuger', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M10', 'ABDUKTORENMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Abduktoren, abductors, Gesäß, glutes', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M11', 'ADDUKTORENMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Adduktoren, adductors', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M12', 'RUMPFROTATION', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Core, Rumpf, schräge Bauchmuskeln, obliques', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M13', 'BUTTERFLY', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Brust, chest, vordere Schulter, front delts, anterior deltoids', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M14', 'REVERSE BUTTERFLY', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'hintere Schulter, rear delts, oberer Rücken, upper back', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M15', 'BIZEPSMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Bizeps, biceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M17', 'SCHULTERPRESSE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Schultern, shoulders, Trizeps, triceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M18', 'TRIZEPSMASCHINE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Trizeps, triceps', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M19', 'HIP THRUST', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Gesäß, glutes, hintere Kette, posterior chain', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Strength', 'M20', 'KNIEBEUGE', 'https://uk.egym.com/en-gb/cloud/strength-equipment', 'https://de.egym.com/de/workouts/smartstrength', 'Quadrizeps, quadriceps, Gesäß, glutes, Hamstrings, Beinbeuger, Core, Rumpf', 'Smart Strength Gerät'),
('smartstrength', 'EGYM Smart Flex', 'SMARTFLEX', 'SMART FLEX', 'https://de.egym.com/de/workouts/smartflex', 'https://de.egym.com/sites/default/files/styles/max_width_750px/public/egym-brand/Icon%20Grid%20Right%20Image%20left/ImageLeftIconRight_SmartFlex_NEW_EN_Mobile_X2_0.jpg?itok=LHrgn9ES', 'Mobilität, Beweglichkeit, mobility, flexibility', 'Mobility-System');

-- Programme und Modi wurden bewusst entfernt.