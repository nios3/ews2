from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for, flash
from simulated_data import get_simulated_data
from models import Location, Alert, SensorReading, WeatherData, CropYield, User, Sensor
from alerts import run_all_checks
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import schedule
import time
import threading
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
import bcrypt

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if unauthorized
@login_manager.user_loader
def load_user(user_id):
    """Load user from the database."""
    session = get_db_session()
    user = session.query(User).get(int(user_id))
    session.close()
    return user
# Database connection
def get_db_session():
    """Get database session"""
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    Session = sessionmaker(bind=engine)
    return Session()

# Function to run scheduled tasks
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Schedule alert checks
def setup_scheduler():
    schedule.every(1).hours.do(run_all_checks)
    # Create a thread for the scheduler
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.route('/')
def home():
    """Home page with EWS information and basemap."""
    session = get_db_session()
    locations = session.query(Location).all()
    session.close()
    return render_template("home.html", locations=locations)

@app.route('/dashboard')
@login_required
def dashboard():
    """EWS Dashboard with real-time data and alerts."""
    session = get_db_session()
    # Get latest data
    locations = session.query(Location).all()
    
    data = {}
    for location in locations:
        # Get latest weather data
        weather = session.query(WeatherData).filter_by(location_id=location.id).order_by(desc(WeatherData.timestamp)).first()
        
        # Get latest soil moisture
        soil_sensor = session.query(Sensor).filter_by(location_id=location.id, sensor_type="soil_moisture").first()
        soil_moisture = None
        if soil_sensor:
            moisture_reading = session.query(SensorReading).filter_by(sensor_id=soil_sensor.id).order_by(desc(SensorReading.timestamp)).first()
            if moisture_reading:
                soil_moisture = moisture_reading.value
        
        # Get latest crop yield prediction
        crop_yield = session.query(CropYield).filter_by(location_id=location.id).order_by(desc(CropYield.timestamp)).first()
        
        # Get active alerts
        alerts = session.query(Alert).filter_by(location_id=location.id, is_active=True).order_by(desc(Alert.timestamp)).all()
        
        # If we have actual data, use it; otherwise use simulated data as fallback
        if not weather or not soil_moisture or not crop_yield:
            simulated = get_simulated_data()
            data[location.name] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weather_data": {
                    "temperature": weather.temperature if weather else simulated["weather_data"]["temperature"],
                    "humidity": weather.humidity if weather else simulated["weather_data"]["humidity"],
                    "rainfall": weather.rainfall if weather else simulated["weather_data"]["rainfall"],
                    "wind_speed": weather.wind_speed if weather else simulated["weather_data"]["wind_speed"],
                    "description": weather.description if weather else simulated["weather_data"]["description"]
                },
                "soil_moisture": {
                    "location": location.name,
                    "moisture_level": soil_moisture if soil_moisture else simulated["soil_moisture"]["moisture_level"]
                },
                "crop_yield": {
                    "location": location.name,
                    "yield_prediction": crop_yield.yield_value if crop_yield else simulated["crop_yield"]["yield_prediction"]
                },
                "alerts": [alert.message for alert in alerts]
            }
        else:
            data[location.name] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weather_data": {
                    "temperature": weather.temperature,
                    "humidity": weather.humidity,
                    "rainfall": weather.rainfall,
                    "wind_speed": weather.wind_speed,
                    "description": weather.description
                },
                "soil_moisture": {
                    "location": location.name,
                    "moisture_level": soil_moisture
                },
                "crop_yield": {
                    "location": location.name,
                    "yield_prediction": crop_yield.yield_value
                },
                "alerts": [alert.message for alert in alerts]
            }
    
    session.close()
    
    # Get the first location data for backward compatibility with your current template
    first_location = next(iter(data.values())) if data else get_simulated_data()
    
    # Sample geoJSON file (zones.geojson) should be in the static folder
    geojson_url = "/static/zones.geojson"
    return render_template("dashboard.html", data=first_location, all_data=data, geojson_url=geojson_url)

@app.route('/downloads')
def downloads():
    """Page for downloading real-time data."""
    # Get data from database
    session = get_db_session()
    
    # Get all sensor readings for the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    sensor_readings = session.query(SensorReading).filter(SensorReading.timestamp > seven_days_ago).all()
    
    # Get all weather data for the last 7 days
    weather_data = session.query(WeatherData).filter(WeatherData.timestamp > seven_days_ago).all()
    
    # Convert to pandas DataFrames
    sensor_df = pd.DataFrame([
        {
            "timestamp": reading.timestamp,
            "sensor_id": reading.sensor_id,
            "value": reading.value
        }
        for reading in sensor_readings
    ])
    
    weather_df = pd.DataFrame([
        {
            "timestamp": data.timestamp,
            "location_id": data.location_id,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "rainfall": data.rainfall,
            "wind_speed": data.wind_speed,
            "description": data.description
        }
        for data in weather_data
    ])
    
    session.close()
    
    # Save DataFrames to CSV
    os.makedirs("static_files", exist_ok=True)
    sensor_csv = "static_files/sensor_data.csv"
    weather_csv = "static_files/weather_data.csv"
    
    sensor_df.to_csv(sensor_csv, index=False)
    weather_df.to_csv(weather_csv, index=False)
    
    return render_template("downloads.html", sensor_csv=sensor_csv, weather_csv=weather_csv)

@app.route('/download/<file_type>/<data_type>')
def download_file(file_type, data_type):
    """Allow downloading data in the chosen format."""
    if data_type == "sensor":
        csv_file = "static_files/sensor_data.csv"
    elif data_type == "weather":
        csv_file = "static_files/weather_data.csv"
    else:
        return "Invalid data type", 400
    
    if file_type == "csv":
        return send_file(csv_file, as_attachment=True)
    elif file_type == "json":
        df = pd.read_csv(csv_file)
        json_file = f"static_files/{data_type}_data.json"
        df.to_json(json_file, orient="records")
        return send_file(json_file, as_attachment=True)
    elif file_type == "excel":
        df = pd.read_csv(csv_file)
        excel_file = f"static_files/{data_type}_data.xlsx"
        df.to_excel(excel_file, index=False)
        return send_file(excel_file, as_attachment=True)
    else:
        return "Invalid file type", 400

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get recent alerts."""
    session = get_db_session()
    alerts = session.query(Alert).filter_by(is_active=True).order_by(desc(Alert.timestamp)).limit(10).all()
    
    alerts_json = [
        {
            "id": alert.id,
            "timestamp": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "location_id": alert.location_id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message
        }
        for alert in alerts
    ]
    
    session.close()
    return jsonify(alerts_json)

@app.route('/api/data/<location_name>')
def get_location_data(location_name):
    """API endpoint to get data for a specific location."""
    session = get_db_session()
    
    location = session.query(Location).filter_by(name=location_name).first()
    if not location:
        session.close()
        return jsonify({"error": "Location not found"}), 404
    
    # Get latest weather data
    weather = session.query(WeatherData).filter_by(location_id=location.id).order_by(desc(WeatherData.timestamp)).first()
    
    # Get latest soil moisture
    soil_sensor = session.query(Sensor).filter_by(location_id=location.id, sensor_type="soil_moisture").first()
    soil_moisture = None
    if soil_sensor:
        moisture_reading = session.query(SensorReading).filter_by(sensor_id=soil_sensor.id).order_by(desc(SensorReading.timestamp)).first()
        if moisture_reading:
            soil_moisture = moisture_reading.value
    
    # Get latest crop yield prediction
    crop_yield = session.query(CropYield).filter_by(location_id=location.id).order_by(desc(CropYield.timestamp)).first()
    
    # Get active alerts
    alerts = session.query(Alert).filter_by(location_id=location.id, is_active=True).order_by(desc(Alert.timestamp)).all()
    
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": {
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude
        },
        "weather_data": {
            "temperature": weather.temperature if weather else None,
            "humidity": weather.humidity if weather else None,
            "rainfall": weather.rainfall if weather else None,
            "wind_speed": weather.wind_speed if weather else None,
            "description": weather.description if weather else None
        },
        "soil_moisture": soil_moisture,
        "crop_yield": crop_yield.yield_value if crop_yield else None,
        "alerts": [
            {
                "timestamp": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message
            }
            for alert in alerts
        ]
    }
    
    session.close()
    return jsonify(data)

@app.route('/Frequent Questions')
def questions():
    return render_template("FAQS.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")


#new
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email

class SignUpForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        session = get_db_session()
        user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        session.add(user)
        session.commit()
        session.close()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = get_db_session()
        user = session.query(User).filter_by(email=form.email.data).first()
        if user and bcrypt.checkpw(form.password.data.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            session.close()
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            session.close()
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# @app.route('/dashboard')

# def dashboard():
#     session = get_db_session()
#     locations = session.query(Location).all()
#     session.close()
#     return render_template("dashboard.html", locations=locations)

@app.route('/more')
def more():
    return render_template('more.html')

if __name__ == '__main__':
    # Set up the scheduler
    setup_scheduler()
    app.run(debug=True, port=3000)