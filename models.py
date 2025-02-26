from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
from flask_login import UserMixin
import bcrypt

Base = declarative_base()

class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String)
    
    # Relationships
    sensors = relationship("Sensor", back_populates="location")
    weather_data = relationship("WeatherData", back_populates="location")
    alerts = relationship("Alert", back_populates="location")
    
    def __repr__(self):
        return f"<Location(name='{self.name}', lat={self.latitude}, lon={self.longitude})>"

class Sensor(Base):
    __tablename__ = 'sensors'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(String, nullable=False, unique=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    sensor_type = Column(String, nullable=False)  # soil_moisture, temperature, etc.
    installation_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    location = relationship("Location", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")
    
    def __repr__(self):
        return f"<Sensor(id='{self.sensor_id}', type='{self.sensor_type}')>"

class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('sensors.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    value = Column(Float, nullable=False)
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")
    
    def __repr__(self):
        return f"<SensorReading(sensor={self.sensor_id}, timestamp={self.timestamp}, value={self.value})>"

class WeatherData(Base):
    __tablename__ = 'weather_data'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    wind_speed = Column(Float)
    description = Column(String)
    
    # Relationships
    location = relationship("Location", back_populates="weather_data")
    
    def __repr__(self):
        return f"<WeatherData(location={self.location_id}, timestamp={self.timestamp})>"

class CropYield(Base):
    __tablename__ = 'crop_yields'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    crop_type = Column(String)
    yield_value = Column(Float)  # kg/ha
    prediction = Column(Boolean, default=True)  # True if predicted, False if actual
    
    def __repr__(self):
        return f"<CropYield(location={self.location_id}, crop='{self.crop_type}', yield={self.yield_value})>"

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey('locations.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    alert_type = Column(String, nullable=False)  # soil_moisture, crop_yield, weather
    severity = Column(String, nullable=False)  # info, warning, critical
    message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    resolved_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False)  # Whether notification has been sent
    
    # Relationships
    location = relationship("Location", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(location={self.location_id}, type='{self.alert_type}', severity='{self.severity}')>"

class User(Base, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    user_type = Column(String)  # farmer, CFA member, admin
    location_id = Column(Integer, ForeignKey('locations.id'))
    alert_preferences = Column(String)  # Could be JSON string with preferences
    password_hash = Column(String(60), nullable=False)  # Add this field for password hashing

    def set_password(self, password):
        """Hash the password and store it."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
