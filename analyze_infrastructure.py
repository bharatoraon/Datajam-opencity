import os
import glob
import pandas as pd
import geopandas as gpd
import fiona
from shapely.geometry import Point, LineString, Polygon
from shapely import force_2d

# Enable KML support in fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'

# Setup paths
BASE_DIR = '/Users/bharatoraon/Desktop/Datajam'
WATER_DIR = os.path.join(BASE_DIR, 'bwssb-water-supply-lines-map-of-bengaluru')
SEWAGE_DIR = os.path.join(BASE_DIR, 'bwssb-sewerage-line-maps-for-bengaluru')
MANHOLES_FILE = 'zip://' + os.path.join(BASE_DIR, 'bwssb-manholes-in-bengaluru', 'manholes.zip')
OUTPUT_FILE = os.path.join(BASE_DIR, 'contamination_risk_zones.geojson')

# Coordinate Reference Systems
CRS_WGS84 = 'EPSG:4326'  # Lat/Lon
CRS_UTM43N = 'EPSG:32643' # Metric for Bengaluru

def load_kmls_from_dir(directory):
    """Load all KML files in a directory and return a combined GeoDataFrame."""
    gdfs = []
    kml_files = glob.glob(os.path.join(directory, '*.kml'))
    print(f"Found {len(kml_files)} KML files in {directory}")
    
    for file in kml_files:
        print(f"  Reading {os.path.basename(file)}...")
        try:
            # KML files can have multiple layers, but usually we just want the first/default one
            gdf = gpd.read_file(file, driver='KML')
            # Force 2D geometry to avoid Z-dimension issues during spatial operations
            gdf.geometry = gdf.geometry.apply(lambda geom: force_2d(geom) if geom else None)
            gdfs.append(gdf)
        except Exception as e:
            print(f"  Error reading {os.path.basename(file)}: {e}")
            
    if gdfs:
        combined = pd.concat(gdfs, ignore_index=True)
        # Drop rows without geometry
        combined = combined[combined.geometry.notnull()]
        return gpd.GeoDataFrame(combined, geometry='geometry', crs=CRS_WGS84)
    else:
        return gpd.GeoDataFrame(columns=['geometry'], crs=CRS_WGS84)

def main():
    print("--- Loading Water Supply Lines ---")
    water_gdf = load_kmls_from_dir(WATER_DIR)
    print(f"Total water supply features: {len(water_gdf)}")
    
    print("\n--- Loading Sewage Lines ---")
    sewage_gdf = load_kmls_from_dir(SEWAGE_DIR)
    print(f"Total sewage line features: {len(sewage_gdf)}")
    
    print("\n--- Loading Manholes ---")
    try:
        manholes_gdf = gpd.read_file(MANHOLES_FILE)
        manholes_gdf.geometry = manholes_gdf.geometry.apply(lambda geom: force_2d(geom) if geom else None)
        print(f"Total manhole features: {len(manholes_gdf)}")
    except Exception as e:
        print(f"Error reading manholes: {e}")
        manholes_gdf = gpd.GeoDataFrame(columns=['geometry'], crs=CRS_WGS84)

    # Need at least water and one of sewage/manholes
    if water_gdf.empty or (sewage_gdf.empty and manholes_gdf.empty):
        print("Not enough data to perform analysis. Exiting.")
        return

    print("\n--- Reprojecting to UTM Zone 43N (Metric) ---")
    water_utm = water_gdf.to_crs(CRS_UTM43N)
    
    sewage_buffered = None
    if not sewage_gdf.empty:
        sewage_utm = sewage_gdf.to_crs(CRS_UTM43N)
        print("Buffering sewage lines by 2 meters...")
        # Create 2m buffer around lines
        sewage_buffer_geom = sewage_utm.geometry.buffer(2)
        sewage_buffered = gpd.GeoDataFrame({'geometry': sewage_buffer_geom, 'source': 'sewage'}, crs=CRS_UTM43N)
        
    manholes_buffered = None
    if not manholes_gdf.empty:
        manholes_utm = manholes_gdf.to_crs(CRS_UTM43N)
        print("Buffering manholes by 2 meters...")
        # Create 2m buffer around points
        manholes_buffer_geom = manholes_utm.geometry.buffer(2)
        manholes_buffered = gpd.GeoDataFrame({'geometry': manholes_buffer_geom, 'source': 'manhole'}, crs=CRS_UTM43N)

    # Combine buffers
    buffers = []
    if sewage_buffered is not None: buffers.append(sewage_buffered)
    if manholes_buffered is not None: buffers.append(manholes_buffered)
    
    combined_buffers = pd.concat(buffers, ignore_index=True)
    combined_buffers_gdf = gpd.GeoDataFrame(combined_buffers, geometry='geometry', crs=CRS_UTM43N)
    
    print("\n--- Performing Spatial Join (Intersection) ---")
    print(f"Checking {len(water_utm)} water supply lines against {len(combined_buffers_gdf)} risk buffers...")
    
    # sjoin will find water supply lines that intersect with the buffers
    # inner join keeps only the water lines that intersect
    at_risk_water_lines = gpd.sjoin(water_utm, combined_buffers_gdf, how='inner', predicate='intersects')
    
    # We might have duplicates if a single water line intersects multiple buffers. We can drop duplicates
    at_risk_water_lines = at_risk_water_lines.drop_duplicates(subset=at_risk_water_lines.geometry.name)
    
    print(f"Found {len(at_risk_water_lines)} water supply pipeline segments at risk of contamination.")
    
    if len(at_risk_water_lines) > 0:
        print("\n--- Saving Results ---")
        # Reproject back to WGS84 for GeoJSON
        at_risk_wgs84 = at_risk_water_lines.to_crs(CRS_WGS84)
        
        # Keep only essential columns to reduce file size
        # KML usually has 'Name' and 'Description'
        cols_to_keep = ['geometry']
        if 'Name' in at_risk_wgs84.columns: cols_to_keep.append('Name')
        if 'source' in at_risk_wgs84.columns: cols_to_keep.append('source')
        
        final_gdf = at_risk_wgs84[cols_to_keep]
        
        print(f"Writing to {OUTPUT_FILE}...")
        final_gdf.to_file(OUTPUT_FILE, driver='GeoJSON')
        print("Analysis complete!")
    else:
        print("No intersecting risk zones found.")

if __name__ == '__main__':
    main()
