import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    csv_path = os.path.join(data_dir, 'Moddata', 'mod-foundation_form-2.csv')
    out_path = os.path.join(base_dir, 'dashboard', 'public', 'Moddata', 'audits.geojson')
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    print("Reading CSV...")
    # Skipping the second header row (index 1) which often messes up column names in kobotoolbox
    df = pd.read_csv(csv_path, skiprows=[1])
    
    # Filter rows that have lat and long
    df = df.dropna(subset=['lat', 'long'])
    
    print(f"Found {len(df)} rows with coordinates.")
    
    geometry = [Point(xy) for xy in zip(df['long'], df['lat'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # Fill NA to prevent GeoJSON export issues
    gdf = gdf.fillna('')
    
    gdf.to_file(out_path, driver='GeoJSON')
    print(f"Saved to {out_path}")

if __name__ == '__main__':
    main()
