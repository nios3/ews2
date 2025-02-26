from models import SensorReading, WeatherData, CropYield, Sensor, Location
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
import random
from datetime import datetime, timedelta
import time
import schedule

def get_db_session():
    """Get database session"""
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    Session = sessionmaker(bind=engine)
    return Session()

def collect_sensor_data():
    """Collect data from sensors and store in database"""
    session = get_db_session()
    
    # Get all active sensors
    sensors = session.query(Sensor).filter_by(is_active=True).all()
    
    readings = []
    for sensor in sensors:
        # Simulate reading based on sensor type
        if sensor.sensor_type == "soil_moisture":
            value = round(random.uniform(10, 40), 2)  # Soil moisture percentage
        elif sensor.sensor_type == "temperature_humidity":
            value = round(random.uniform(15, 35), 2)  # Temperature in Celsius
        else:
            value = round(random.uniform(0, 100), 2)  # Generic value
        
        reading = SensorReading(
            sensor_id=sensor.id,
            timestamp=datetime.now(),
            value=value
        )
        readings.append(reading)
    
    session.add_all(readings)
    session.commit()
    session.close()
    return f"Collected {len(readings)} sensor readings"

def collect_weather_data():
    """Collect weather data and store in database"""
    session = get_db_session()
    
    # Get all locations
    locations = session.query(Location).all()
    
    weather_data = []
    for location in locations:
        temperature = round(random.uniform(15, 35), 2)
        humidity = round(random.uniform(30, 90), 2)
        rainfall = round(random.uniform(0, 50), 2) if random.random() < 0.3 else 0  # 30% chance of rain
        wind_speed = round(random.uniform(0, 20), 2)
        
        # Determine weather description based on conditions
        if rainfall > 10:
            description = "Rainy"
        elif rainfall > 0:
            description = "Light Rain"
        elif temperature > 30:
            description = "Hot"
        elif humidity > 80:
            description = "Humid"
        else:
            description = "Clear"
        
        weather = WeatherData(
            location_id=location.id,
            timestamp=datetime.now(),
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            wind_speed=wind_speed,
            description=description
        )
        weather_data.append(weather)
    
    session.add_all(weather_data)
    session.commit()
    session.close()
    return f"Collected weather data for {len(weather_data)} locations"

def predict_crop_yields():
    """Generate crop yield predictions and store in database"""
    session = get_db_session()
    
    # Get all locations
    locations = session.query(Location).all()
    
    crops = ["Maize", "Beans", "Rice", "Wheat", "Coffee"]
    predictions = []
    
    for location in locations:
        # Get latest soil moisture for this location
        soil_sensor = session.query(Sensor).filter_by(location_id=location.id, sensor_type="soil_moisture").first()
        moisture = None
        if soil_sensor:
            moisture_reading = session.query(SensorReading).filter_by(sensor_id=soil_sensor.id).order_by(SensorReading.timestamp.desc()).first()
            if moisture_reading:
                moisture = moisture_reading.value
        
        # Get latest weather data for this location
        weather = session.query(WeatherData).filter_by(location_id=location.id).order_by(WeatherData.timestamp.desc()).first()
        
        # Generate predictions for each crop type
        for crop in crops:
            # Base yield varies by crop type
            base_yield = {
                "Maize": random.uniform(3.5, 7),
                "Beans": random.uniform(0.8, 2.5),
                "Rice": random.uniform(4, 9),
                "Wheat": random.uniform(2.5, 6),
                "Coffee": random.uniform(0.5, 1.5)
            }[crop]
            
            # Adjust yield based on environmental factors
            if moisture is not None:
                # Optimal moisture varies by crop
                optimal_moisture = {
                    "Maize": 30,
                    "Beans": 25,
                    "Rice": 35,
                    "Wheat": 22,
                    "Coffee": 28
                }[crop]
                
                # Adjust yield based on moisture difference from optimal
                moisture_diff = abs(moisture - optimal_moisture)
                moisture_factor = max(0.7, 1 - (moisture_diff / 100))
                base_yield *= moisture_factor
            
            # Adjust for weather if available
            if weather:
                # Temperature factor
                optimal_temp = {
                    "Maize": 25,
                    "Beans": 23,
                    "Rice": 27,
                    "Wheat": 20,
                    "Coffee": 22
                }[crop]
                
                temp_diff = abs(weather.temperature - optimal_temp)
                temp_factor = max(0.7, 1 - (temp_diff / 50))
                base_yield *= temp_factor
                
                # Rainfall factor - varies by crop
                if crop == "Rice":
                    # Rice benefits more from rainfall
                    rainfall_factor = min(1.3, 1 + (weather.rainfall / 100))
                else:
                    # Too much rain can be bad for other crops
                    optimal_rain = {
                        "Maize": 15,
                        "Beans": 10,
                        "Wheat": 12,
                        "Coffee": 20
                    }[crop]
                    rain_diff = abs(weather.rainfall - optimal_rain)
                    rainfall_factor = max(0.8, 1 - (rain_diff / 50))
                
                base_yield *= rainfall_factor
            
            # Add some randomness to simulate real-world variability
            yield_prediction = round(base_yield * random.uniform(0.9, 1.1), 2)
            
            prediction = CropYield(
                location_id=location.id,
                crop_type=crop,
                # prediction_date=datetime.now(),
                # predicted_yield=yield_prediction,  # Tons per hectare
                # confidence=random.uniform(0.7, 0.95)  # Confidence score
            )
            predictions.append(prediction)
    
    session.add_all(predictions)
    session.commit()
    session.close()
    return f"Generated {len(predictions)} crop yield predictions"

def initialize_database():
    """Initialize database with some sample sensors and locations if empty"""
    session = get_db_session()
    
    # Check if we already have locations
    if session.query(Location).count() == 0:
        # Create sample locations
        locations = [
            Location(name="North Farm", latitude=1.2345, longitude=36.8765, elevation=1800, area=150),
            Location(name="South Valley", latitude=1.1234, longitude=36.7654, elevation=1650, area=200),
            Location(name="East Highlands", latitude=1.3456, longitude=36.9876, elevation=2100, area=120),
            Location(name="West Plains", latitude=1.0123, longitude=36.5432, elevation=1500, area=250)
        ]
        session.add_all(locations)
        session.commit()
        
        # Create sensors for each location
        sensors = []
        for location in locations:
            # Each location gets a soil moisture sensor
            sensors.append(
                Sensor(
                    location_id=location.id,
                    sensor_type="soil_moisture",
                    installation_date=datetime.now() - timedelta(days=random.randint(10, 100)),
                    last_maintenance_date=datetime.now() - timedelta(days=random.randint(0, 10)),
                    is_active=True
                )
            )
            
            # Each location gets a temperature/humidity sensor
            sensors.append(
                Sensor(
                    location_id=location.id,
                    sensor_type="temperature_humidity",
                    installation_date=datetime.now() - timedelta(days=random.randint(10, 100)),
                    last_maintenance_date=datetime.now() - timedelta(days=random.randint(0, 10)),
                    is_active=True
                )
            )
            
            # 50% chance of a third sensor for other measurements
            if random.random() > 0.5:
                sensors.append(
                    Sensor(
                        location_id=location.id,
                        sensor_type=random.choice(["light", "soil_ph", "wind"]),
                        installation_date=datetime.now() - timedelta(days=random.randint(10, 100)),
                        last_maintenance_date=datetime.now() - timedelta(days=random.randint(0, 10)),
                        is_active=True
                    )
                )
        
        session.add_all(sensors)
        session.commit()
        print(f"Initialized database with {len(locations)} locations and {len(sensors)} sensors")
    
    session.close()

def run_scheduler():
    """Set up and run the scheduler for regular data collection"""
    # Initialize database first
    initialize_database()
    
    # Schedule tasks
    schedule.every(1).hour.do(collect_sensor_data)
    schedule.every(3).hours.do(collect_weather_data)
    schedule.every(1).days.at("00:00").do(predict_crop_yields)
    
    # Run tasks immediately for initial data
    print("Performing initial data collection...")
    collect_sensor_data()
    collect_weather_data()
    predict_crop_yields()
    
    print("Scheduler running. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_scheduler()