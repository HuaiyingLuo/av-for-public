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
    # Add a new column 'id'
    return data

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

    # Get all files in sample-data
    samples = [f for f in os.listdir('sample-data') if f.endswith('.csv')]

    for sample in samples:
        sample_path = f"sample-data/{sample}"
        batch_index = sample.split('_')[-1].split('.')[0]
        data = load_data(sample_path)
        results = []
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc=f"Processing batch {batch_index}"):
            logging.info(f"Processing batch {batch_index}")
            pickup = f"{row['pickup_latitude']},{row['pickup_longitude']}"
            dropoff = f"{row['dropoff_latitude']},{row['dropoff_longitude']}"
            route = get_route(pickup, dropoff, API_KEY, ENDPOINT)
            if route and 'routes' in route and route['routes']:
                decoded_points = decode(route['routes'][0]['overview_polyline']['points'])
                swapped_points = [[lng, lat] for lat, lng in decoded_points]
                if 1 < len(swapped_points) < 25: 
                    # Polyline points should have at least 2 points
                    # Maximum of 25 Waypoints Per Request
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
            save_results_to_csv(results, f"pu-routes/trip_201306_{batch_index}.csv")
            save_results_to_geojson(results, f"pu-routes/trip_201306_{batch_index}.geojson")
            print(f"Batch {batch_index} saved")
            logging.info(f"Batch {batch_index} saved")

    print("All routes saved")

if __name__ == "__main__":
    main()

