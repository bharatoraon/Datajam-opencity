import geopandas as gpd

files = [
    '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata/raw_water.geojson',
    '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata/raw_sewage.geojson',
    '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata/raw_manholes.geojson'
]

for file in files:
    print(f"Simplifying {file}...")
    gdf = gpd.read_file(file)
    gdf = gdf[['geometry']]
    gdf.to_file(file, driver='GeoJSON')
    print(f"Done {file}")
