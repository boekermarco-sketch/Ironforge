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
('plate_loaded', 'MAGNUM', 'MG-PL33 LAT PULLDOWN', 'https://de.matrixfitness.com/deu/strength/plate-loaded/mg-pl33-lat-pulldown', 'https://www.usmedrehab.com/cdn/shop/products/matrix-magnum-lat-pulldown.png', 'Latissimus, oberer Rücken, Bizeps', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL62 SMITH MACHINE', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl62-smith-machine', 'https://www.getsomefitnessequipment.com/cdn/shop/products/matrix-mg-pl62-smith-machine.png', 'Ganzkörper, Beine, Brust, Schultern', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL70 45-DEGREE LEG PRESS', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl70-45-degree-leg-press', 'https://www.usmedrehab.com/cdn/shop/products/matrix-magnum-45-degree-leg-press.png', 'Quadrizeps, Gesäß, Hamstrings', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL71 HACK SQUAT', 'https://world.matrixfitness.com/eng/strength/plate-loaded/mg-pl71-hack-squat', 'https://www.usmedrehab.com/cdn/shop/products/matrix-magnum-hack-squat.png', 'Quadrizeps, Gesäß, Hamstrings', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL78 GLUTE TRAINER', 'https://de.matrixfitness.com/deu/strength/plate-loaded/mg-pl78-glute-trainer', 'https://www.usmedrehab.com/cdn/shop/products/matrix-magnum-glute-trainer.png', 'Gesäß, hintere Kette', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'MG-PL79 SQUAT / LUNGE', 'https://de.matrixfitness.com/deu/strength/plate-loaded/mg-pl79-squat-lunge', 'https://www.usmedrehab.com/cdn/shop/products/matrix-magnum-squat-lunge.png', 'Quadrizeps, Gesäß, Hamstrings', 'Plate-loaded'),
('plate_loaded', 'MAGNUM', 'VY-401 LEG EXTENSION', 'https://world.matrixfitness.com/eng/strength/plate-loaded/vy-401-leg-extension', 'https://www.usmedrehab.com/cdn/shop/products/matrix-vy-401-leg-extension.png', 'Quadrizeps', 'Plate-loaded'),

('single_station', 'G1', 'G1-MS20 ADJUSTABLE CABLE CROSSOVER', 'https://uk.matrixfitness.com/eng/strength/multi-station/g1-ms20-adjustable-cable-crossover', 'https://www.usmedrehab.com/cdn/shop/products/matrix-g1-ms20-adjustable-cable-crossover.png', 'Brust, Schultern, Rücken, Core', 'Single-station'),
('single_station', 'G1', 'G1-MG30 3-STACK MULTI-GYM', 'https://world.matrixfitness.com/eng/strength/multi-station/g1-mg30-3-stack', 'https://www.getsomefitnessequipment.com/cdn/shop/products/matrix-g1-mg30-3-stack-multi-gym.png', 'Ganzkörper', 'Single-station / Multi-gym'),
('single_station', 'G1', 'G1 SERIES', 'https://de.matrixfitness.com/deu/strength/g1', 'https://www.usmedrehab.com/cdn/shop/products/matrix-g1-series.png', 'Ganzkörper', 'Serienseite'),
('single_station', 'G1', 'G7-S71 LEG EXTENSION', 'https://us.matrixfitness.com/eng/strength/single-station/g7-s71-leg-extension', 'https://www.usmedrehab.com/cdn/shop/products/g7-s71.png', 'Quadrizeps', 'ArchiExpo reference'),
('single_station', 'G1', 'G7-S73 LEG CURL', 'https://world.matrixfitness.com/eng/strength/single-station/g7-s73-prone-leg-curl', 'https://www.usmedrehab.com/cdn/shop/products/g7-s73.png', 'Hamstrings', 'ArchiExpo reference'),

('multi_station', 'AURA', 'AURA 4-STACK MULTI-STATION', 'https://www.johnsonfitness.com/Matrix-Aura-4-Stack-Multi-Station-P38106.aspx', 'https://images.jhtassets.com/66de8374cc4e3d27b3c3d83e71923f0c4fc2a51d/original/named/Aura4StackMultiStation+385+tur+tr+rnSatSayfas.pdf', 'Ganzkörper', 'Multi-station'),
('multi_station', 'AURA', 'AURA 5-STACK MULTI-STATION', 'https://johnsonfitness.co.nz/products/matrix-aura-5-stack-multi-station', 'https://images.jhtassets.com/92f5dbbf3baff3b2a0b9762db2a2505100fd0af5/original/named/Aura5StackMultiStation+386+en+us+ProductSellSheet.pdf', 'Ganzkörper', 'Multi-station'),
('multi_station', 'AURA', 'AURA 8-STACK MULTI-STATION', 'https://commercial.fitnessexperience.ca/products/matrix-aura-8-stack-multi-station', 'https://images.jhtassets.com/0e73d60ee809c50554e06805e53ef20f8d157bef/original/named/Aura8StackMultiStation.pdf', 'Ganzkörper', 'Multi-station'),
('multi_station', 'AURA', 'AURA ADJUSTABLE CABLE CROSSOVER', 'https://world.matrixfitness.com/eng/strength/multi-station/g3-ms20-adjustable-cable-crossover', 'https://images.jhtassets.com/5079cbfb443ef55191cb969ce1e34d753acee405/original/named/AuraAdjustableCableCrossover.pdf', 'Brust, Schultern, Rücken, Core', 'Multi-station');
