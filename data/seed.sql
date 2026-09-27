-- Dummy data for testing

INSERT INTO facility (name, kind, capacity, attrs, geom) VALUES
('Nongpoh Highway Center', 'truck_bay', 120, '{"food": true, "fuel": true}', ST_GeomFromText('POINT(91.88 25.90)', 4326)),
('Umsning Fuel & Rest', 'truck_bay', 40, '{"food": true}', ST_GeomFromText('POINT(91.89 25.75)', 4326)),
('Jowai Truck Terminal', 'truck_bay', 200, '{"medical": true}', ST_GeomFromText('POINT(92.20 25.45)', 4326));

INSERT INTO incident (occurred_on, kind, duration_hours, source_url, geom) VALUES
('2023-06-15', 'landslide', 48.0, 'https://pib.gov.in/example1', ST_GeomFromText('POINT(91.90 25.70)', 4326)),
('2022-08-10', 'flood', 24.0, 'https://pib.gov.in/example2', ST_GeomFromText('POINT(92.10 25.50)', 4326));
