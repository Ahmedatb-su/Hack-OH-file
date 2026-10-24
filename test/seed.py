"""Seed demo locations: python -m scripts.seed"""
from app.database import Base, SessionLocal, engine
from app.models import Location

DEMO = [
    ("CABS Bus 1", "bus", 60),
    ("CABS Bus 2", "bus", 60),
    ("COTA Route 2 - High St", "bus", 40),
    ("Union Food Court", "food_court", 250),
    ("Kennedy Commons", "food_court", 300),
]

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for name, kind, cap in DEMO:
            if not db.query(Location).filter_by(name=name).first():
                db.add(Location(name=name, kind=kind, capacity=cap))
        db.commit()
    print("Seeded.")
