import os
from dotenv import load_dotenv
import requests
import pandas as pd
import polyline
import geopandas as gpd
from shapely.geometry import LineString
from polyline import decode
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    filename="log/getRoutes.log",
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_data(file_path):
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()  # Remove whitespace from column names
    print("Data loaded successfully")
    return data.sample(n=2)

def fetch_route_data(data, api_key, endpoint):
    results = []
    for index, row in tqdm(data.iterrows(), total=data.shape[0], desc="Fetching routes"):
        pickup = f"{row['pickup_latitude']},{row['pickup_longitude']}"
        dropoff = f"{row['dropoff_latitude']},{row['dropoff_longitude']}"
        route = get_route(pickup, dropoff, api_key, endpoint)
        if route and 'routes' in route and route['routes']:
            decoded_points = decode(route['routes'][0]['overview_polyline']['points'])
            swapped_points = [[lng, lat] for lat, lng in decoded_points]
            results.append({
                'Pickup': pickup,
                'Dropoff': dropoff,
                'Polyline_Points': swapped_points,
            })
        else:
            print(f"No route found for {pickup} to {dropoff}")
            logging.error(f"No route found for {pickup} to {dropoff}")
    return results

def save_results_to_csv(results, file_path):
    results_df = pd.DataFrame(results)
    results_df.to_csv(file_path, index=False)

def save_results_to_geojson(results, file_path):
    geometries = [LineString(result['Polyline_Points']) for result in results]
    geo_df = pd.DataFrame(results)[['Pickup', 'Dropoff']]
    gdf = gpd.GeoDataFrame(geo_df, geometry=geometries)
    gdf.set_crs(epsg=4326, inplace=True)
    gdf.to_file(file_path, driver="GeoJSON")

def get_route(pickup, dropoff, api_key, endpoint):
    params = {
        'origin': pickup,
        'destination': dropoff,
        'mode': 'driving',
        'key': api_key
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        return None

def main():
    # Load environment variables
    load_dotenv()
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise ValueError("API key not found. Please set the GOOGLE_MAPS_API_KEY environment variable.")
    
    ENDPOINT = 'https://maps.googleapis.com/maps/api/directions/json'
    
    # Load and process data
    # TODO: Change the data file name 
    data = load_data('pu-data/trip_data_6.csv')
    results = fetch_route_data(data, API_KEY, ENDPOINT)
    
    # Save results
    # TODO: Change the output file name
    save_results_to_csv(results, "pu-routes/trip_routes_201306.csv")
    save_results_to_geojson(results, "pu-routes/trip_routes_201306.geojson")
    print("All routes saved")

if __name__ == "__main__":
    main()

