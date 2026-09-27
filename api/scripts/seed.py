import os
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import Facility, Incident

def seed_db():
    print("Creating tables (SQLite)...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Seed Truck Bays
    if db.query(Facility).count() == 0:
        print("Seeding facilities...")
        facilities = [
            Facility(name='Nongpoh Highway Center', kind='truck_bay', capacity=120),
            Facility(name='Umsning Fuel & Rest', kind='truck_bay', capacity=40),
            Facility(name='Jowai Truck Terminal', kind='truck_bay', capacity=200)
        ]
        db.add_all(facilities)
        db.commit()

    # Seed Historical Incidents
    if db.query(Incident).count() == 0:
        print("Seeding historical incidents...")
        incidents = [
            Incident(kind='landslide', duration_hours=48.0, source_url='https://pib.gov.in/example1'),
            Incident(kind='flood', duration_hours=24.0, source_url='https://pib.gov.in/example2'),
            Incident(kind='blockade', duration_hours=12.0, source_url='https://pib.gov.in/example3')
        ]
        db.add_all(incidents)
        db.commit()

    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
