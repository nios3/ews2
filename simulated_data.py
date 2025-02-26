import random
from datetime import datetime

def get_simulated_data():
    """Simulates data for soil moisture, crop yield, and weather."""
    weather_data = {
        "temperature": round(random.uniform(15, 35), 2),  # °C
        "humidity": round(random.uniform(30, 90), 2),     # %
        "rainfall": round(random.uniform(0, 50), 2),      # mm
        "wind_speed": round(random.uniform(0, 20), 2),    # km/h
        "description": random.choice(["Clear", "Rainy", "Stormy", "Cloudy"]),
    }

    soil_moisture = {"location": "Farm A", "moisture_level": round(random.uniform(5, 35), 2)}  # %

    crop_yield = {"location": "Farm A", "yield_prediction": round(random.uniform(100, 400), 2)}  # kg/ha

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "weather_data": weather_data,
        "soil_moisture": soil_moisture,
        "crop_yield": crop_yield,
    }
