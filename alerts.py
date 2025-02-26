from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from models import Alert, SensorReading, WeatherData, CropYield, Location, User, Sensor
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from twilio.rest import Client
import json

# Thresholds
SOIL_MOISTURE_LOW = 15.0  # %
SOIL_MOISTURE_HIGH = 35.0  # %
TEMPERATURE_HIGH = 35.0  # °C
RAINFALL_HEAVY = 50.0  # mm
CROP_YIELD_CRITICAL = 150.0  # kg/ha

def get_db_session():
    """Get database session"""
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    Session = sessionmaker(bind=engine)
    return Session()

def check_soil_moisture_alerts():
    """Check soil moisture readings and generate alerts if needed"""
    session = get_db_session()
    
    # Get active soil moisture sensors
    soil_sensors = session.query(Sensor).filter_by(sensor_type="soil_moisture", is_active=True).all()
    
    alerts = []
    for sensor in soil_sensors:
        # Get most recent reading
        reading = session.query(SensorReading).filter_by(sensor_id=sensor.id).order_by(desc(SensorReading.timestamp)).first()
        
        if reading:
            location = sensor.location
            
            if reading.value < SOIL_MOISTURE_LOW:
                # Create low moisture alert
                alert = Alert(
                    location_id=location.id,
                    alert_type="soil_moisture",
                    severity="warning",
                    message=f"Low soil moisture detected at {location.name}: {reading.value}%. Water your crops immediately."
                )
                alerts.append(alert)
            elif reading.value > SOIL_MOISTURE_HIGH:
                # Create high moisture alert
                alert = Alert(
                    location_id=location.id,
                    alert_type="soil_moisture",
                    severity="info",
                    message=f"High soil moisture detected at {location.name}: {reading.value}%. Consider reducing irrigation."
                )
                alerts.append(alert)
    
    if alerts:
        session.add_all(alerts)
        session.commit()
    
    session.close()
    return alerts

def check_weather_alerts():
    """Check weather data and generate alerts if needed"""
    session = get_db_session()
    
    # Get most recent weather data for each location
    locations = session.query(Location).all()
    
    alerts = []
    for location in locations:
        weather = session.query(WeatherData).filter_by(location_id=location.id).order_by(desc(WeatherData.timestamp)).first()
        
        if weather:
            # Check for extreme temperature
            if weather.temperature > TEMPERATURE_HIGH:
                alert = Alert(
                    location_id=location.id,
                    alert_type="weather",
                    severity="warning",
                    message=f"High temperature alert at {location.name}: {weather.temperature}°C. Protect sensitive crops and ensure adequate irrigation."
                )
                alerts.append(alert)
            
            # Check for heavy rainfall
            if weather.rainfall > RAINFALL_HEAVY:
                alert = Alert(
                    location_id=location.id,
                    alert_type="weather",
                    severity="critical",
                    message=f"Heavy rainfall alert at {location.name}: {weather.rainfall}mm. Watch for flooding and ensure proper drainage."
                )
                alerts.append(alert)
    
    if alerts:
        session.add_all(alerts)
        session.commit()
    
    session.close()
    return alerts

def check_crop_yield_alerts():
    """Check crop yield predictions and generate alerts if needed"""
    session = get_db_session()
    
    # Get most recent crop yield predictions for each location
    locations = session.query(Location).all()
    
    alerts = []
    for location in locations:
        yield_data = session.query(CropYield).filter_by(location_id=location.id, prediction=True).order_by(desc(CropYield.timestamp)).first()
        
        if yield_data and yield_data.yield_value < CROP_YIELD_CRITICAL:
            alert = Alert(
                location_id=location.id,
                alert_type="crop_yield",
                severity="critical",
                message=f"Low crop yield prediction for {location.name}: {yield_data.yield_value} kg/ha for {yield_data.crop_type}. Consider soil testing and consultation with agricultural extension officers."
            )
            alerts.append(alert)
    
    if alerts:
        session.add_all(alerts)
        session.commit()
    
    session.close()
    return alerts

def send_sms_alerts():
    """Send SMS notifications for active alerts that haven't been sent yet"""
    session = get_db_session()
    
    # Get unsent active alerts
    unsent_alerts = session.query(Alert).filter_by(is_active=True, is_sent=False).all()
    
    if not unsent_alerts:
        session.close()
        return "No new alerts to send"
    
    # Initialize Twilio client
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"Error initializing Twilio client: {e}")
        session.close()
        return f"Failed to initialize Twilio: {e}"
    
    sent_count = 0
    for alert in unsent_alerts:
        # Get users associated with this location
        location = session.query(Location).get(alert.location_id)
        users = session.query(User).filter_by(location_id=alert.location_id).all()
        
        for user in users:
            # Check if user has preferences and wants this type of alert
            send_to_user = True
            if user.alert_preferences:
                try:
                    preferences = json.loads(user.alert_preferences)
                    if alert.alert_type in preferences and not preferences[alert.alert_type]:
                        send_to_user = False
                except json.JSONDecodeError:
                    # If preferences are invalid JSON, assume user wants all alerts
                    pass
            
            if send_to_user and user.phone:
                try:
                    message = client.messages.create(
                        body=alert.message,
                        from_=TWILIO_PHONE_NUMBER,
                        to=user.phone
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending SMS to {user.phone}: {e}")
        
        # Mark alert as sent
        alert.is_sent = True
    
    session.commit()
    session.close()
    return f"Sent {sent_count} SMS alerts"

def run_all_checks():
    """Run all alert checks and send notifications"""
    soil_alerts = check_soil_moisture_alerts()
    weather_alerts = check_weather_alerts()
    crop_alerts = check_crop_yield_alerts()
    
    total_alerts = len(soil_alerts) + len(weather_alerts) + len(crop_alerts)
    if total_alerts > 0:
        send_result = send_sms_alerts()
        return f"Generated {total_alerts} alerts. {send_result}"
    else:
        return "No new alerts generated"

if __name__ == "__main__":
    print(run_all_checks())