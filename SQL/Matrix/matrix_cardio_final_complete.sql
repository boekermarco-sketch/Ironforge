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
('cardio', 'PERFORMANCE', 'TREADMILL', 'https://world.matrixfitness.com/eng/cardio/catalog', 'images/002_programmable-treadmill.jpg', 'Treadmill', 'AC dynamic response drive, incline, low step-on height', 'Curated: one representative cardio type'),
('cardio', 'PERFORMANCE', 'ELLIPTICAL', 'https://world.matrixfitness.com/eng/cardio/catalog', 'images/007_commercial-elliptical-trainer.jpg', 'Elliptical', 'Suspension design, wheel-free, low noise', 'Curated: one representative cardio type'),
('cardio', 'PERFORMANCE', 'CLIMBMILL', 'https://world.matrixfitness.com/eng/cardio/catalog', 'images/016_commercial-stepper.jpg', 'Climbmill', 'Vertical climbing motion, high intensity', 'Curated: one representative cardio type'),
('cardio', 'PERFORMANCE', 'UPRIGHT BIKE', 'https://world.matrixfitness.com/eng/cardio/catalog', 'images/018_commercial-exercise-bike.jpg', 'Cycle', 'Commercial upright cycle', 'Curated: one representative cardio type'),
('cardio', 'PERFORMANCE', 'ROWER', 'https://world.matrixfitness.com/eng/group-training/cardio/rower', 'images/060_magnetic-rowing-machine.jpg', 'Rower', 'Aluminum flywheel, magnetic resistance', 'Curated: one representative cardio type');
