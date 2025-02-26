from flask import Flask, render_template, send_file
from simulated_data import get_simulated_data
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def home():
    """Home page with EWS information and basemap."""
    return render_template("home.html")

@app.route('/dashboard')
def dashboard():
    """EWS Dashboard with real-time data and alerts."""
    data = get_simulated_data()
    # Sample geoJSON file (zones.geojson) should be in the static folder
    geojson_url = "/static/zones.geojson"
    return render_template("dashboard.html", data=data, geojson_url=geojson_url)

@app.route('/downloads')
def downloads():
    """Page for downloading real-time data."""
    # Generate simulated real-time data
    data = get_simulated_data()
    df = pd.DataFrame([data["weather_data"], data["soil_moisture"], data["crop_yield"]])
    csv_file = "static_files/data.csv"
    df.to_csv(csv_file, index=False)
    return render_template("downloads.html", csv_url=csv_file)

@app.route('/download/<format>')
def download_file(format):
    """Allow downloading data in the chosen format."""
    csv_file = "static_files/data.csv"
    if format == "csv":
        return send_file(csv_file, as_attachment=True)
    elif format == "json":
        df = pd.read_csv(csv_file)
        json_file = "static_files/data.json"
        df.to_json(json_file, orient="records")
        return send_file(json_file, as_attachment=True)
    elif format == "excel":
        df = pd.read_csv(csv_file)
        excel_file = "static_files/data.xlsx"
        df.to_excel(excel_file, index=False)
        return send_file(excel_file, as_attachment=True)

@app.route('/Frequent Questions')
def questions():
    return render_template("FAQS.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/more')
def more():
    return render_template('more.html')



if __name__ == '__main__':
    app.run(debug=True,port=3000)
