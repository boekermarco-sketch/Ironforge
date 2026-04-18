CREATE TABLE IF NOT EXISTS matrix_cardio_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    serie VARCHAR(100),
    model VARCHAR(255) NOT NULL,
    product_url TEXT,
    image_url TEXT,
    cardio_type VARCHAR(100),
    features TEXT,
    notes TEXT
);

INSERT INTO matrix_cardio_devices (category, serie, model, product_url, image_url, cardio_type, features, notes) VALUES
('cardio', 'PERFORMANCE', 'TREADMILL', 'https://world.matrixfitness.com/eng', 'https://de.matrixfitness.com/deu/cardio/catalog?modalities=treadmills&series=performance', 'Treadmill', 'AC dynamic response drive, incline, low step-on height', 'Performance family'),
('cardio', 'LIFESTYLE', 'TREADMILL', 'https://world.matrixfitness.com/eng', 'https://de.matrixfitness.com/deu/cardio/catalog?modalities=treadmills', 'Treadmill', 'Space-saving design, smooth drive system, low step-on height', 'Lifestyle family'),
('cardio', 'ENDURANCE', 'TREADMILL', 'https://de.matrixfitness.com/deu/cardio/catalog?series=endurance', 'https://de.matrixfitness.com/deu/cardio/catalog?series=endurance', 'Treadmill', 'Commercial treadmill platform', 'Endurance family'),
('cardio', 'PERFORMANCE', 'ELLIPTICAL', 'https://world.matrixfitness.com/eng', 'https://world.matrixfitness.com/eng/cardio/catalog', 'Elliptical', 'Suspension design, wheel-free, low noise', 'Performance family'),
('cardio', 'PERFORMANCE', 'ASCENT TRAINER', 'https://world.matrixfitness.com/eng', 'https://world.matrixfitness.com/eng/cardio/catalog', 'Climb trainer', 'Adjustable incline, variable stride length', 'Performance family'),
('cardio', 'PERFORMANCE', 'CLIMBMILL', 'https://world.matrixfitness.com/eng', 'https://world.matrixfitness.com/eng/cardio/catalog', 'Stair climber', 'Vertical climbing motion, high intensity', 'Performance family'),
('cardio', 'PERFORMANCE', 'RECUMBENT CYCLE', 'https://world.matrixfitness.com/eng', 'https://world.matrixfitness.com/eng/cardio/catalog', 'Recumbent bike', 'Low-impact, accessible seated design', 'Performance family'),
('cardio', 'PERFORMANCE', 'UPRIGHT BIKE', 'https://world.matrixfitness.com/eng', 'https://world.matrixfitness.com/eng/cardio/catalog', 'Upright bike', 'Commercial upright cycle', 'Performance family'),
('cardio', 'PERFORMANCE', 'ROWER', 'https://world.matrixfitness.com/eng/group-training/cardio/rower', 'https://world.matrixfitness.com/eng/group-training/cardio/rower', 'Rower', 'Aluminum flywheel, magnetic resistance', 'Low-impact full-body cardio'),
('cardio', 'ENDURANCE', 'ELLIPTICAL', 'https://de.matrixfitness.com/deu/cardio/catalog?series=endurance', 'https://de.matrixfitness.com/deu/cardio/catalog?series=endurance', 'Elliptical', 'Commercial elliptical platform', 'Endurance family'),
('cardio', 'ENDURANCE', 'CYCLE', 'https://de.matrixfitness.com/deu/cardio/catalog?modalities=cycles&series=endurance', 'https://de.matrixfitness.com/deu/cardio/catalog?modalities=cycles&series=endurance', 'Bike', 'Commercial cycle platform', 'Endurance family'),
('cardio', 'ENDURANCE', 'ROWER', 'https://world.matrixfitness.com/eng/group-training/cardio/rower', 'https://world.matrixfitness.com/eng/group-training/cardio/rower', 'Rower', 'Low-impact full-body rower', 'Endurance family'),
('cardio', 'LIFESTYLE', 'ELLIPTICAL', 'https://matrixhomefitness.com/collections/cardio', 'https://matrixhomefitness.com/collections/cardio', 'Elliptical', 'Home and light commercial cardio', 'Lifestyle family'),
('cardio', 'LIFESTYLE', 'BIKE', 'https://matrixhomefitness.com/collections/cardio', 'https://matrixhomefitness.com/collections/cardio', 'Bike', 'Upright or recumbent depending on model', 'Lifestyle family'),
('cardio', 'LIFESTYLE', 'ROWER', 'https://matrixhomefitness.com/collections/cardio', 'https://matrixhomefitness.com/collections/cardio', 'Rower', 'Low-impact cardio rower', 'Lifestyle family');
