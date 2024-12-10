import os
from dotenv import load_dotenv
import requests
import pandas as pd
import polyline
import geopandas as gpd
from shapely.geometry import LineString
from polyline import decode
import logging

# Set up logging
logging.basicConfig(
    filename="log/getRoutes.log",
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Load environment variables from .env file
load_dotenv()

# TODO: Load your data
data = pd.read_csv('pu-data/other-Federal_02216.csv')

# TODO: Filter for a time period: July 2014
data = data[data['Date'].str.contains(r'07/\d{2}/2014')]

# TODO: Set up API key and base URL
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
    if route and 'routes' in route and route['routes']:

        decoded_points = decode(route['routes'][0]['overview_polyline']['points'])
        swapped_points = [[lng, lat] for lat, lng in decoded_points]

        results.append({
            'Date': date,
            'Time': time,
            'Pickup_Address': pickup,
            'Dropoff_Address': dropoff,
            'Polyline_Points': swapped_points,
        })
    else:
        print(f"No route found for {pickup} to {dropoff}")
        logging.error(f"No route found for {pickup} to {dropoff}")
        
# Save as csv file
# TODO: Change the file name and path
results_df = pd.DataFrame(results)
print(results_df.columns)
results_df.to_csv("pu-routes/trip_routes_07.csv", index=False)

# Save as geojson file
# TODO: Change the file name and path
geometries = []
for result in results:
    line = LineString(result['Polyline_Points'])
    geometries.append(line)
geo_df = results_df[['Date', 'Time', 'Pickup_Address', 'Dropoff_Address']]
gdf = gpd.GeoDataFrame(geo_df, geometry=geometries)
gdf.set_crs(epsg=4326, inplace=True)
gdf.to_file("pu-routes/trip_routes_07.geojson", driver="GeoJSON")
print("All routes saved")

