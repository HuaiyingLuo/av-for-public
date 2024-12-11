import os
import pandas as pd
import geopandas as gpd

result = gpd.GeoDataFrame()

for file in os.listdir('pu-routes'):
    if file.endswith('.geojson'):
        gdf = gpd.read_file(f'pu-routes/{file}')
        result = pd.concat([result, gdf], ignore_index=True)

# Save result
result.to_file('pu-routes/trip_201306.geojson', driver='GeoJSON')
        
