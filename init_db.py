from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Location, Sensor, User
import os
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
import bcrypt

# Create database connection
def get_engine():
    return create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add default admin user
    if session.query(User).count() == 0:
        admin = User(
            name="Admin",
            email="admin@example.com",
            password_hash=bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            user_type="admin"
        )
        session.add(admin)
        session.commit()

    session.close()
    return "Database initialized with sample data"
def init_db():
    """Initialize database tables and add initial data"""
    engine = get_engine()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if we already have locations, if not, add some default ones
    if session.query(Location).count() == 0:
        # Add some sample locations
        locations = [
            Location(name="Farm A", latitude=-1.286389, longitude=36.817223, description="Sample farm near Nairobi"),
            Location(name="Forest B", latitude=-0.023559, longitude=37.906193, description="Sample forest site"),
            Location(name="Farm C", latitude=0.514277, longitude=35.269779, description="Sample farm in Eldoret region")
        ]
        session.add_all(locations)
        session.commit()
        
        # Add some sample sensors
        sensors = []
        for loc in locations:
            sensors.append(Sensor(sensor_id=f"SM_{loc.name}_001", location_id=loc.id, sensor_type="soil_moisture"))
            sensors.append(Sensor(sensor_id=f"TH_{loc.name}_001", location_id=loc.id, sensor_type="temperature_humidity"))
        
        session.add_all(sensors)
        session.commit()
    
    session.close()
    return "Database initialized with sample data"

if __name__ == "__main__":
    print(init_db())