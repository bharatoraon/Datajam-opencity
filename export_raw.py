import os
import geopandas as gpd
from analyze_infrastructure import load_kmls_from_dir, WATER_DIR, SEWAGE_DIR, MANHOLES_FILE, CRS_WGS84, force_2d

out_dir = '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata'

# Water
w = load_kmls_from_dir(WATER_DIR)
w.to_file(os.path.join(out_dir, 'raw_water.geojson'), driver='GeoJSON')
print(f"Water: {len(w)} features")

# Sewage
s = load_kmls_from_dir(SEWAGE_DIR)
s.to_file(os.path.join(out_dir, 'raw_sewage.geojson'), driver='GeoJSON')
print(f"Sewage: {len(s)} features")

# Manholes
m = gpd.read_file(MANHOLES_FILE)
m.geometry = m.geometry.apply(lambda geom: force_2d(geom) if geom else None)
m = m.to_crs(CRS_WGS84)
m.to_file(os.path.join(out_dir, 'raw_manholes.geojson'), driver='GeoJSON')
print(f"Manholes: {len(m)} features")
