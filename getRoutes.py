import os
import urllib.parse
from dotenv import load_dotenv
import requests
import pandas as pd
import polyline
import geopandas as gpd
from shapely.geometry import LineString

# Load environment variables from .env file
load_dotenv()

# Load your data
data = pd.read_csv('pu-data/other-Federal_02216.csv')

# Filter for July 2014
data = data[data['Date'].str.contains('2014-07')]

# API key and base URL
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise ValueError("API key not found. Please set the GOOGLE_MAPS_API_KEY environment variable.")

URL = 'https://maps.googleapis.com/maps/api/directions/json'

# Function to fetch route details
def get_route(pickup, dropoff):
    params = {
        'origin': pickup,
        'destination': dropoff,
        'key': API_KEY
    }
    response = requests.get(URL, params=params)
    print("response status code: ", response.status_code)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Iterate through records and fetch data
results = []
for index, row in data.iterrows():
    date = row['Date']
    time = row['Time']
    pickup = row['PU_Address']
    dropoff = row['DO_Address']
    route = get_route(pickup, dropoff)
    if route:
        results.append({
            'Date': date,
            'Time': time,
            'Pickup_Address': pickup,
            'Dropoff_Address': dropoff,
            'Polyline_Points': polyline.decode(route['routes'][0]['overview_polyline']['points']),
        })
    else:
        print(f"No route found for {pickup} to {dropoff}")

results_df = pd.DataFrame(results)
results_df.to_csv("pu-routes/trip_routes_07.csv", index=False)

# Create a GeoDataFrame with geometries
geometries = []
for result in results:
    line = LineString(result['Polyline_Points'])
    geometries.append(line)
geo_df = results_df[['Date', 'Time', 'Pickup_Address', 'Dropoff_Address']]
gdf = gpd.GeoDataFrame(geo_df, geometry=geometries)
gdf.set_crs(epsg=4326, inplace=True)
gdf.to_file("pu-routes/trip_routes_07.geojson", driver="GeoJSON")

