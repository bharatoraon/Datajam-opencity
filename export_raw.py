import os
import geopandas as gpd
from analyze_infrastructure import (
    BASE_DIR,
    load_kmls_from_dir,
    WATER_DIR,
    SEWAGE_DIR,
    CRS_WGS84,
    force_2d,
    resolve_manholes_file,
)

out_dir = os.path.join(BASE_DIR, 'dashboard', 'public', 'Moddata')
os.makedirs(out_dir, exist_ok=True)

# Water
w = load_kmls_from_dir(WATER_DIR)
w.to_file(os.path.join(out_dir, 'raw_water.geojson'), driver='GeoJSON')
print(f"Water: {len(w)} features")

# Sewage
s = load_kmls_from_dir(SEWAGE_DIR)
s.to_file(os.path.join(out_dir, 'raw_sewage.geojson'), driver='GeoJSON')
print(f"Sewage: {len(s)} features")

# Manholes
m = gpd.read_file(resolve_manholes_file())
m.geometry = m.geometry.apply(lambda geom: force_2d(geom) if geom else None)
m = m.to_crs(CRS_WGS84)
m.to_file(os.path.join(out_dir, 'raw_manholes.geojson'), driver='GeoJSON')
print(f"Manholes: {len(m)} features")
