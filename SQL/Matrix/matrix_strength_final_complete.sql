CREATE TABLE IF NOT EXISTS matrix_strength_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    serie VARCHAR(100),
    model VARCHAR(255) NOT NULL,
    product_url TEXT,
    image_url TEXT,
    muscle_groups TEXT,
    notes TEXT
);

INSERT INTO matrix_strength_devices (category, serie, model, product_url, image_url, muscle_groups, notes) VALUES
('plate_loaded', 'MAGNUM', 'MG-PL12 VERTICAL BENCH PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl12-vertical-bench-press', 'images/043_press-weight-training-machine.jpg', 'Brust, chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL13 SUPINE BENCH PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl13-supine-bench-press', 'images/041_commercial-weight-bench.jpg', 'Brust, chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL14 INCLINE BENCH PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl14-incline-bench-press', 'images/042_adjustable-weight-bench.jpg', 'obere Brust, upper chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL15 VERTICAL DECLINE BENCH PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl15-vertical-decline-bench-press', 'images/044_adjustable-weight-bench.jpg', 'untere Brust, lower chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL23 SHOULDER PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl23-shoulder-press', 'images/024_press-weight-training-machine.jpg', 'Schultern, shoulders, Trizeps, triceps', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL33 LAT PULLDOWN', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl33-lat-pulldown', 'images/022_lat-pulldown-weight-training-machine.jpg', 'Latissimus, lats, oberer Rücken, upper back, Bizeps, biceps', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL41 ELEVATED BICEPS CURL', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl41-elevated-biceps-curl', 'images/023_curl-weight-training-machine.jpg', 'Bizeps, biceps', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL50 AB CRUNCH BENCH', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl50-ab-crunch-bench', 'images/025_abdominal-crunch-weight-training-machine.jpg', 'Bauchmuskeln, abs, abdominals', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL62 SMITH MACHINE (MULTIPRESSE)', 'https://www.johnsonfitness.com.au/products/matrix-mg-smith-machine', 'images/030_multifunction-fitness-machine.jpg', 'Ganzkörper, full body, Beine, legs, Brust, chest, Schultern, shoulders', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL70 45-DEGREE LEG PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl70-45-degree-leg-press', 'images/027_leg-press-weight-training-machine.jpg', 'Quadrizeps, quadriceps, Gesäß, glutes, Hamstrings, Beinbeuger', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL72 KNEELING LEG CURL', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl72-kneeling-leg-curl', 'images/029_leg-curl-weight-training-machine.jpg', 'Hamstrings, Beinbeuger', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL73 RECLINING LEG EXTENSION', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl73-reclining-leg-extension', 'images/028_leg-extension-weight-training-machine.jpg', 'Quadrizeps, quadriceps', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL77 SEATED CALF', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl77-seated-calf', 'images/047_calf-weight-training-machine.jpg', 'Waden, calves, calf', 'Plate-loaded'),

('single_station', 'ULTRA', 'G7-S13 CONVERGING CHEST PRESS', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s13-converging-chest-press', 'images/024_press-weight-training-machine.jpg', 'Brust, chest, Trizeps, triceps, vordere Schulter, front delts, anterior deltoids', 'Single-station'),
('single_station', 'ULTRA', 'G7-S33 DIVERGING LAT PULLDOWN', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s33-diverging-lat-pulldown', 'images/022_lat-pulldown-weight-training-machine.jpg', 'Latissimus, lats, oberer Rücken, upper back, Bizeps, biceps', 'Single-station'),
('single_station', 'ULTRA', 'G7-S40 INDEPENDENT BICEPS CURL', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s40-independent-biceps-curl', 'images/023_curl-weight-training-machine.jpg', 'Bizeps, biceps', 'Single-station'),
('single_station', 'ULTRA', 'G7-S42 TRICEPS PRESS', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s42-triceps-press', 'images/024_press-weight-training-machine.jpg', 'Trizeps, triceps', 'Single-station'),
('single_station', 'ULTRA', 'G7-S51 ABDOMINAL CRUNCH', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s51-abdominal-crunch', 'images/025_abdominal-crunch-weight-training-machine.jpg', 'Bauchmuskeln, abs, abdominals', 'Single-station'),
('single_station', 'ULTRA', 'G7-S55 ROTARY TORSO', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s55-rotary-torso', 'images/026_rotary-torso-weight-training-machine.jpg', 'Core, Rumpf, schräge Bauchmuskeln, obliques', 'Single-station'),
('single_station', 'ULTRA', 'G7-S70 LEG PRESS', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s70-leg-press', 'images/027_leg-press-weight-training-machine.jpg', 'Quadrizeps, quadriceps, Gesäß, glutes, Hamstrings, Beinbeuger', 'Single-station'),
('single_station', 'ULTRA', 'G7-S71 LEG EXTENSION', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s71-leg-extension', 'images/028_leg-extension-weight-training-machine.jpg', 'Quadrizeps, quadriceps', 'Single-station'),
('single_station', 'ULTRA', 'G7-S73 PRONE LEG CURL', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s73-prone-leg-curl', 'images/029_leg-curl-weight-training-machine.jpg', 'Hamstrings, Beinbeuger', 'Single-station');
