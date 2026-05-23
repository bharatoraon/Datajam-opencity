import os
import geopandas as gpd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODDATA_DIR = os.path.join(BASE_DIR, 'dashboard', 'public', 'Moddata')

files = [
    os.path.join(MODDATA_DIR, 'raw_water.geojson'),
    os.path.join(MODDATA_DIR, 'raw_sewage.geojson'),
    os.path.join(MODDATA_DIR, 'raw_manholes.geojson')
]

for file in files:
    print(f"Simplifying {file}...")
    gdf = gpd.read_file(file)
    gdf = gdf[['geometry']]
    gdf.to_file(file, driver='GeoJSON')
    print(f"Done {file}")
