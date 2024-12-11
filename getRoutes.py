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

def load_data(file_path, sample_size):
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()  # Remove whitespace from column names
    print("Data loaded successfully")
    # Add a new column 'id'
    data['id'] = range(data.shape[0])
    return data.sample(n=sample_size)

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

def save_results_to_csv(results, file_path):
    results_df = pd.DataFrame(results)
    results_df.to_csv(file_path, index=False)

def save_results_to_geojson(results, file_path):
    geometries = [LineString(result['Polyline_Points']) for result in results]
    geo_df = pd.DataFrame(results)[['id', 'Pickup', 'Dropoff']]
    gdf = gpd.GeoDataFrame(geo_df, geometry=geometries)
    gdf.set_crs(epsg=4326, inplace=True)
    gdf.to_file(file_path, driver="GeoJSON")

def main():
    # Load environment variables
    load_dotenv()
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise ValueError("API key not found. Please set the GOOGLE_MAPS_API_KEY environment variable.")
    
    ENDPOINT = 'https://maps.googleapis.com/maps/api/directions/json'
    
    # Load and process data
    # TODO: Change data file name and sample size
    data = load_data('pu-data/trip_data_6.csv', sample_size=40000)
    
    # Batch processing logic 
    total_records = data.shape[0]
    # TODO: Change batch size
    batch_size = 2000
    for start in range(0, total_records, batch_size):
        end = min(start + batch_size, total_records)
        batch_data = data.iloc[start:end]
        results = []
        for index, row in tqdm(batch_data.iterrows(), total=batch_data.shape[0], desc=f"Fetching routes {start}-{end}"):
            pickup = f"{row['pickup_latitude']},{row['pickup_longitude']}"
            dropoff = f"{row['dropoff_latitude']},{row['dropoff_longitude']}"
            route = get_route(pickup, dropoff, API_KEY, ENDPOINT)
            if route and 'routes' in route and route['routes']:
                decoded_points = decode(route['routes'][0]['overview_polyline']['points'])
                swapped_points = [[lng, lat] for lat, lng in decoded_points]
                if len(swapped_points) > 1: # Polyline points should have at least 2 points
                    results.append({
                        'id': row['id'],
                        'Pickup': pickup,
                        'Dropoff': dropoff,
                        'Polyline_Points': swapped_points,
                    })
            else:
                print(f"No route found for record {row['id']}")
                logging.error(f"No route found for record {row['id']}")
        
        # Save results for the current batch
        save_results_to_csv(results, f"pu-routes/trip_201306_batch_{start}_{end}.csv")
        save_results_to_geojson(results, f"pu-routes/trip_201306_batch_{start}_{end}.geojson")
        print(f"Batch {start}-{end} saved")

    print("All routes saved")

if __name__ == "__main__":
    main()

