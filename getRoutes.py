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
    return data.sample(n=40000)

def fetch_route_data_in_batches(data, api_key, endpoint, batch_size=2000):
    total_records = data.shape[0]
    for start in range(0, total_records, batch_size):
        end = min(start + batch_size, total_records)
        batch_data = data.iloc[start:end]
        results = []
        for index, row in tqdm(batch_data.iterrows(), total=batch_data.shape[0], desc=f"Fetching routes {start}-{end}"):
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
        
        # Save results for the current batch
        save_results_to_csv(results, f"pu-routes/trip_routes_batch_{start}_{end}.csv")
        save_results_to_geojson(results, f"pu-routes/trip_routes_batch_{start}_{end}.geojson")
        print(f"Batch {start}-{end} saved")

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
    results = fetch_route_data_in_batches(data, API_KEY, ENDPOINT)
    
    # Save results
    # TODO: Change the output file name
    save_results_to_csv(results, "pu-routes/trip_routes_201306.csv")
    save_results_to_geojson(results, "pu-routes/trip_routes_201306.geojson")
    print("All routes saved")

if __name__ == "__main__":
    main()

