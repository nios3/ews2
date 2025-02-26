import geopandas as gpd

# Load the shapefile
shapefile_path = r"F:\DEVELOPMENT_\ews-flask\DATA\FARMERS DETAILS\FARMERS_DETAILS.shp"
geo_data = gpd.read_file(shapefile_path)

# Save to GeoJSON
geojson_path = "F_DETAILS.geojson"
geo_data.to_file(geojson_path, driver="GeoJSON")

print(f"Shapefile has been converted to GeoJSON and saved at {geojson_path}")
