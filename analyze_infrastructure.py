import os
import glob
import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
import fiona
from shapely.geometry import Point, LineString, Polygon
from shapely import force_2d

# Enable KML support in fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
WATER_DIR = os.path.join(DATA_DIR, 'bwssb-water-supply-lines-map-of-bengaluru')
SEWAGE_DIR = os.path.join(DATA_DIR, 'bwssb-sewerage-line-maps-for-bengaluru')
MANHOLES_DIR = os.path.join(DATA_DIR, 'bwssb-manholes-in-bengaluru')
MANHOLES_FILE = 'zip://' + os.path.join(MANHOLES_DIR, 'manholes.zip')
OUTPUT_FILE = os.path.join(BASE_DIR, 'contamination_risk_zones.geojson')
DASHBOARD_PUBLIC_DIR = os.path.join(BASE_DIR, 'dashboard', 'public')
DASHBOARD_DIST_DIR = os.path.join(BASE_DIR, 'dashboard', 'dist')
MODDATA_DIRS = [
    os.path.join(DASHBOARD_PUBLIC_DIR, 'Moddata'),
    os.path.join(DASHBOARD_DIST_DIR, 'Moddata'),
    os.path.join(BASE_DIR, 'Moddata'),
    os.path.join(DATA_DIR, 'Moddata'),
]

# Coordinate Reference Systems
CRS_WGS84 = 'EPSG:4326'  # Lat/Lon
CRS_UTM43N = 'EPSG:32643' # Metric for Bengaluru
KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}

TYPOLOGY_SCORES = {
    # Higher values mark stronger human exposure or sensitive receptors beside drains.
    't4': 22,  # Property adjacent, abutting buildings
    't5': 18,  # Property adjacent, with setback
    't8': 18,  # Inside private property / campus
    't6': 16,  # Lake adjacent with pathway
    't7': 16,  # Lake adjacent without pathway, if added later
    't2': 12,  # Road adjacent without footpath
    't3': 12,  # Ring road / highway
    't1': 8,   # Road adjacent with footpath
    't10': 8,  # Open space adjacent
    't11': 4,  # Agricultural land adjacent
    't12': 4,  # Vacant land adjacent
}

OUTPUT_COLUMNS = [
    'risk_score',
    'risk_category',
    'risk_factors',
    'source_exposure_score',
    'sewage_score',
    'sewage_distance_m',
    'manhole_score',
    'manhole_distance_m',
    'audit_score',
    'audit_count_50m',
    'audit_evidence',
    'typology_score',
    'typology_codes',
    'typology_names',
    'receptor_score',
    'receptor_distance_m',
    'water_supply_score',
    'water_supply_distance_m',
    'slum_score',
    'slum_distance_m',
    'drain_class',
    'drain_id',
    'ward_name',
    'valley',
    'subvalley',
    'length_m',
]

def parse_kml_coordinates(text):
    """Parse a KML coordinate block into lon/lat tuples."""
    coords = []
    for item in (text or '').split():
        parts = item.split(',')
        if len(parts) < 2:
            continue
        try:
            coords.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return coords

def load_kml_with_xml(file):
    """Fallback KML reader for files that GeoPandas/GDAL cannot parse."""
    rows = []
    root = ET.parse(file).getroot()

    for placemark in root.findall('.//kml:Placemark', KML_NS):
        name_elem = placemark.find('kml:name', KML_NS)
        name = name_elem.text if name_elem is not None else None

        for point in placemark.findall('.//kml:Point/kml:coordinates', KML_NS):
            coords = parse_kml_coordinates(point.text)
            if coords:
                rows.append({'Name': name, 'geometry': Point(coords[0])})

        for line in placemark.findall('.//kml:LineString/kml:coordinates', KML_NS):
            coords = parse_kml_coordinates(line.text)
            if len(coords) >= 2:
                rows.append({'Name': name, 'geometry': LineString(coords)})

        for ring in placemark.findall('.//kml:Polygon//kml:outerBoundaryIs//kml:LinearRing/kml:coordinates', KML_NS):
            coords = parse_kml_coordinates(ring.text)
            if len(coords) >= 3:
                rows.append({'Name': name, 'geometry': Polygon(coords)})

    return gpd.GeoDataFrame(rows, geometry='geometry', crs=CRS_WGS84)

def load_kmls_from_dir(directory):
    """Load all KML files in a directory and return a combined GeoDataFrame."""
    gdfs = []
    kml_files = glob.glob(os.path.join(directory, '**', '*.kml'), recursive=True)
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
            print(f"  GeoPandas error reading {os.path.basename(file)}: {e}")
            print("  Trying XML fallback parser...")
            try:
                gdf = load_kml_with_xml(file)
                print(f"  XML fallback loaded {len(gdf)} features.")
                gdfs.append(gdf)
            except Exception as fallback_error:
                print(f"  Error reading {os.path.basename(file)}: {fallback_error}")
            
    if gdfs:
        combined = pd.concat(gdfs, ignore_index=True)
        # Drop rows without geometry
        combined = combined[combined.geometry.notnull()]
        return gpd.GeoDataFrame(combined, geometry='geometry', crs=CRS_WGS84)
    else:
        return gpd.GeoDataFrame(columns=['geometry'], crs=CRS_WGS84)

def resolve_manholes_file():
    """Return the manholes dataset path from the downloaded OpenCity folder."""
    if os.path.exists(os.path.join(MANHOLES_DIR, 'manholes.zip')):
        return MANHOLES_FILE

    for pattern in ('*.zip', '*.geojson', '*.json', '*.shp', '*.gpkg', '*.kml'):
        matches = glob.glob(os.path.join(MANHOLES_DIR, '**', pattern), recursive=True)
        if matches:
            path = matches[0]
            return 'zip://' + path if path.endswith('.zip') else path

    return MANHOLES_FILE

def empty_geodataframe(crs=CRS_WGS84):
    """Return an empty GeoDataFrame with the expected geometry column."""
    return gpd.GeoDataFrame(columns=['geometry'], geometry='geometry', crs=crs)

def has_kml_files(directory):
    return bool(glob.glob(os.path.join(directory, '**', '*.kml'), recursive=True))

def find_moddata_file(filename):
    """Find a dashboard/data layer in the current repo layout."""
    for directory in MODDATA_DIRS:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
    return None

def clean_geometries(gdf, crs=CRS_WGS84):
    """Normalize CRS, strip Z values, and drop empty geometries."""
    if gdf is None or gdf.empty:
        return empty_geodataframe(crs)

    if gdf.crs is None:
        gdf = gdf.set_crs(crs)
    gdf = gdf.copy()
    gdf.geometry = gdf.geometry.apply(lambda geom: force_2d(geom) if geom else None)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty]
    return gpd.GeoDataFrame(gdf, geometry='geometry', crs=gdf.crs)

def read_vector(path, label, required=False):
    """Read a GeoJSON/shapefile/KML-like vector layer if it exists."""
    if not path:
        if required:
            print(f"Missing required layer: {label}")
        else:
            print(f"Optional layer unavailable: {label}")
        return empty_geodataframe()

    print(f"Reading {label} from {path}...")
    try:
        gdf = gpd.read_file(path)
        gdf = clean_geometries(gdf)
        print(f"  {label}: {len(gdf)} features")
        return gdf
    except Exception as exc:
        message = f"Error reading {label}: {exc}"
        if required:
            raise RuntimeError(message) from exc
        print(message)
        return empty_geodataframe()

def load_water_supply():
    if has_kml_files(WATER_DIR):
        return load_kmls_from_dir(WATER_DIR)
    return read_vector(find_moddata_file('raw_water.geojson'), 'exported water supply')

def load_sewage():
    if has_kml_files(SEWAGE_DIR):
        return load_kmls_from_dir(SEWAGE_DIR)
    return read_vector(find_moddata_file('raw_sewage.geojson'), 'exported sewage')

def load_manholes():
    if os.path.exists(MANHOLES_DIR) and glob.glob(os.path.join(MANHOLES_DIR, '**', '*'), recursive=True):
        return read_vector(resolve_manholes_file(), 'manholes')
    return read_vector(find_moddata_file('raw_manholes.geojson'), 'exported manholes')

def load_drains():
    layers = []
    primary = read_vector(find_moddata_file('mod-foundation_primarydrains.geojson'), 'primary drains')
    if not primary.empty:
        primary['drain_class'] = 'primary'
        layers.append(primary)

    secondary = read_vector(find_moddata_file('mod-foundation_secondarydrains.geojson'), 'secondary drains')
    if not secondary.empty:
        secondary['drain_class'] = 'secondary'
        layers.append(secondary)

    if not layers:
        return empty_geodataframe()

    drains = gpd.GeoDataFrame(pd.concat(layers, ignore_index=True), geometry='geometry', crs=layers[0].crs)
    drains = clean_geometries(drains, drains.crs)
    drains['drain_id'] = drains.apply(select_drain_id, axis=1)
    return drains

def select_drain_id(row):
    for column in ('Drain num', 'sec_id', 'pri_id', 'id', 'fid'):
        value = row.get(column)
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return None

def normalize_text(value):
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()

def distance_band_score(distance, bands):
    if pd.isna(distance):
        return 0
    for threshold, score in bands:
        if distance <= threshold:
            return score
    return 0

def risk_category(score):
    if score >= 75:
        return 'Very High'
    if score >= 55:
        return 'High'
    if score >= 35:
        return 'Moderate'
    if score >= 20:
        return 'Elevated'
    return 'Low'

def nearest_features(left, right, max_distance, distance_col, columns=None):
    """Return one nearest right-side feature per left feature."""
    columns = columns or []
    if left.empty or right.empty:
        return pd.DataFrame(index=left.index)

    left_work = left[['geometry']].copy()
    left_work['_risk_index'] = left.index
    right_cols = [column for column in columns if column in right.columns]
    right_work = right[right_cols + ['geometry']].copy()

    joined = gpd.sjoin_nearest(
        left_work,
        right_work,
        how='left',
        max_distance=max_distance,
        distance_col=distance_col,
    )
    joined = joined.sort_values(['_risk_index', distance_col], na_position='last')
    return joined.drop_duplicates('_risk_index').set_index('_risk_index')

def add_nearest_distance(drains, layer, column, max_distance, source_columns=None):
    nearest = nearest_features(drains, layer, max_distance, column, source_columns)
    drains[column] = nearest.get(column, pd.Series(index=drains.index, dtype='float64')).reindex(drains.index)
    return drains

def aggregate_typology(drains, typology):
    drains['typology_score'] = 0
    drains['typology_codes'] = ''
    drains['typology_names'] = ''

    if typology.empty or 'typ' not in typology.columns:
        return drains

    typology = typology.copy()
    typology['typ'] = typology['typ'].apply(normalize_text)
    typology['_typology_score'] = typology['typ'].map(TYPOLOGY_SCORES).fillna(0).astype(int)

    buffered = gpd.GeoDataFrame(
        {'_risk_index': drains.index},
        geometry=drains.geometry.buffer(5),
        crs=drains.crs,
    )
    join_cols = ['typ', '_typology_score', 'geometry']
    if 'typology_name' in typology.columns:
        join_cols.insert(1, 'typology_name')

    joined = gpd.sjoin(buffered, typology[join_cols], how='left', predicate='intersects')
    joined = joined[joined['index_right'].notna()]
    if joined.empty:
        return drains

    def unique_join(values):
        clean = sorted({normalize_text(value) for value in values if normalize_text(value)})
        return ', '.join(clean[:6])

    aggregations = {
        '_typology_score': 'max',
        'typ': unique_join,
    }
    if 'typology_name' in joined.columns:
        aggregations['typology_name'] = unique_join

    grouped = joined.groupby('_risk_index').agg(aggregations)
    drains.loc[grouped.index, 'typology_score'] = grouped['_typology_score'].astype(int)
    drains.loc[grouped.index, 'typology_codes'] = grouped['typ']
    if 'typology_name' in grouped.columns:
        drains.loc[grouped.index, 'typology_names'] = grouped['typology_name']
    return drains

def score_audit(row):
    contamination = normalize_text(row.get('water_contamination')).lower()
    unauthorised = normalize_text(row.get('unauthorised_inlets')).lower()
    stagnant = normalize_text(row.get('water_stagnant')).lower()
    smell = normalize_text(row.get('water_smell')).lower()

    score = 0
    if 'black' in contamination or 'grey' in contamination:
        score += 20
    elif 'oily' in contamination or 'solid' in contamination:
        score += 15
    elif 'froth' in contamination or 'foam' in contamination:
        score += 12
    elif 'cannot see' in contamination:
        score += 8

    if unauthorised and unauthorised not in {'no', 'none', 'na', 'n/a'}:
        score += 12
    if stagnant and stagnant not in {'no', 'none', 'na', 'n/a'}:
        score += 5
    if smell and smell not in {'no', 'none', 'na', 'n/a'}:
        score += 5

    return min(score, 30)

def aggregate_audits(drains, audits):
    drains['audit_score'] = 0
    drains['audit_count_50m'] = 0
    drains['audit_evidence'] = ''

    if audits.empty:
        return drains

    audits = audits.copy()
    audits['_audit_score'] = audits.apply(score_audit, axis=1)
    buffered = gpd.GeoDataFrame(
        {'_risk_index': drains.index},
        geometry=drains.geometry.buffer(50),
        crs=drains.crs,
    )

    audit_cols = ['_audit_score', 'geometry']
    for column in ('water_contamination', 'unauthorised_inlets'):
        if column in audits.columns:
            audit_cols.insert(-1, column)

    joined = gpd.sjoin(buffered, audits[audit_cols], how='left', predicate='intersects')
    joined = joined[joined['index_right'].notna()]
    if joined.empty:
        return drains

    def evidence(values):
        clean = sorted({normalize_text(value) for value in values if normalize_text(value)})
        return ', '.join(clean[:4])

    grouped = joined.groupby('_risk_index').agg(
        audit_score=('_audit_score', 'max'),
        audit_count_50m=('_audit_score', 'count'),
    )
    if 'water_contamination' in joined.columns:
        grouped['audit_evidence'] = joined.groupby('_risk_index')['water_contamination'].agg(evidence)

    drains.loc[grouped.index, 'audit_score'] = grouped['audit_score'].fillna(0).astype(int)
    drains.loc[grouped.index, 'audit_count_50m'] = grouped['audit_count_50m'].fillna(0).astype(int)
    if 'audit_evidence' in grouped.columns:
        drains.loc[grouped.index, 'audit_evidence'] = grouped['audit_evidence']
    return drains

def combine_optional_layers(layers):
    valid_layers = [layer for layer in layers if layer is not None and not layer.empty]
    if not valid_layers:
        return empty_geodataframe()
    return gpd.GeoDataFrame(pd.concat(valid_layers, ignore_index=True), geometry='geometry', crs=valid_layers[0].crs)

def hotspot_point(geometry):
    if geometry is None or geometry.is_empty:
        return None
    try:
        return geometry.interpolate(0.5, normalized=True)
    except Exception:
        return geometry.representative_point()

def build_risk_reasons(row):
    reasons = []
    if row.get('sewage_score', 0) >= 40:
        reasons.append('sewage line overlaps or is within 5 m of drain')
    elif row.get('sewage_score', 0) > 0:
        reasons.append('sewage line near drain')
    if row.get('manhole_score', 0) > 0:
        reasons.append('manholes near drain')
    if row.get('audit_score', 0) > 0:
        reasons.append('field audit contamination evidence')
    if row.get('typology_score', 0) > 0 and row.get('typology_codes'):
        reasons.append(f"exposed drain typology: {row.get('typology_codes')}")
    if row.get('receptor_score', 0) > 0:
        reasons.append('lake or wetland receptor nearby')
    if row.get('slum_score', 0) > 0:
        reasons.append('slum settlement nearby')
    if row.get('water_supply_score', 0) > 0:
        reasons.append('water supply asset nearby')
    return '; '.join(reasons)

def calculate_contamination_risk():
    print("--- Loading Risk Inputs ---")
    drains = load_drains()
    sewage = load_sewage()
    manholes = load_manholes()
    water_supply = load_water_supply()
    typology = read_vector(find_moddata_file('mod-foundation_typology_analysis.geojson'), 'drain typology')
    audits = read_vector(find_moddata_file('audits.geojson'), 'citizen audits')
    lakes = read_vector(find_moddata_file('mod-foundation_lakes_existing.geojson'), 'existing lakes')
    wetlands = read_vector(find_moddata_file('mod-foundation_wetlands.geojson'), 'wetlands')
    slums = read_vector(find_moddata_file('slums.geojson'), 'slums')

    if drains.empty or sewage.empty:
        print("Need at least drains and sewage data to calculate contamination hotspots. Exiting.")
        return empty_geodataframe()

    print("\n--- Reprojecting to UTM Zone 43N (Metric) ---")
    drains_utm = drains.to_crs(CRS_UTM43N).reset_index(drop=True)
    sewage_utm = sewage.to_crs(CRS_UTM43N)
    manholes_utm = manholes.to_crs(CRS_UTM43N) if not manholes.empty else manholes
    water_utm = water_supply.to_crs(CRS_UTM43N) if not water_supply.empty else water_supply
    typology_utm = typology.to_crs(CRS_UTM43N) if not typology.empty else typology
    audits_utm = audits.to_crs(CRS_UTM43N) if not audits.empty else audits
    receptors_utm = combine_optional_layers([
        lakes.to_crs(CRS_UTM43N) if not lakes.empty else lakes,
        wetlands.to_crs(CRS_UTM43N) if not wetlands.empty else wetlands,
    ])
    slums_utm = slums.to_crs(CRS_UTM43N) if not slums.empty else slums

    print("\n--- Calculating Proximity and Evidence Scores ---")
    drains_utm = add_nearest_distance(drains_utm, sewage_utm, 'sewage_distance_m', 30)
    drains_utm = add_nearest_distance(drains_utm, manholes_utm, 'manhole_distance_m', 30)
    drains_utm = add_nearest_distance(drains_utm, water_utm, 'water_supply_distance_m', 30)
    drains_utm = add_nearest_distance(drains_utm, receptors_utm, 'receptor_distance_m', 100)
    drains_utm = add_nearest_distance(drains_utm, slums_utm, 'slum_distance_m', 250)

    drains_utm = aggregate_typology(drains_utm, typology_utm)
    drains_utm = aggregate_audits(drains_utm, audits_utm)

    drains_utm['sewage_score'] = drains_utm['sewage_distance_m'].apply(
        lambda distance: distance_band_score(distance, [(5, 45), (15, 30), (30, 15)])
    )
    drains_utm['manhole_score'] = drains_utm['manhole_distance_m'].apply(
        lambda distance: distance_band_score(distance, [(5, 18), (15, 12), (30, 6)])
    )
    drains_utm['water_supply_score'] = drains_utm['water_supply_distance_m'].apply(
        lambda distance: distance_band_score(distance, [(5, 10), (15, 6), (30, 3)])
    )
    drains_utm['receptor_score'] = drains_utm['receptor_distance_m'].apply(
        lambda distance: distance_band_score(distance, [(50, 12), (100, 6)])
    )
    drains_utm['slum_score'] = drains_utm['slum_distance_m'].apply(
        lambda distance: distance_band_score(distance, [(50, 18), (100, 10), (250, 5)])
    )

    drains_utm['source_exposure_score'] = (
        drains_utm['sewage_score']
        + drains_utm['manhole_score']
        + drains_utm['audit_score']
    )
    drains_utm['risk_score'] = (
        drains_utm['source_exposure_score']
        + drains_utm['typology_score']
        + drains_utm['water_supply_score']
        + drains_utm['receptor_score']
        + drains_utm['slum_score']
    ).clip(upper=100).round().astype(int)
    drains_utm['risk_category'] = drains_utm['risk_score'].apply(risk_category)
    drains_utm['risk_factors'] = drains_utm.apply(build_risk_reasons, axis=1)

    risk_drains = drains_utm[drains_utm['source_exposure_score'] > 0].copy()
    print(f"Calculated {len(risk_drains)} drain contamination hotspot candidates.")

    if risk_drains.empty:
        return empty_geodataframe()

    risk_points = risk_drains.copy()
    risk_points.geometry = risk_points.geometry.apply(hotspot_point)
    risk_points = clean_geometries(risk_points, CRS_UTM43N)

    for column in ('sewage_distance_m', 'manhole_distance_m', 'water_supply_distance_m', 'receptor_distance_m', 'slum_distance_m'):
        if column in risk_points.columns:
            risk_points[column] = risk_points[column].round(1)

    cols = ['geometry'] + [column for column in OUTPUT_COLUMNS if column in risk_points.columns]
    return risk_points[cols].to_crs(CRS_WGS84)

def write_outputs(gdf):
    paths = [
        OUTPUT_FILE,
        os.path.join(DASHBOARD_PUBLIC_DIR, 'contamination_risk_zones.geojson'),
    ]
    if os.path.exists(DASHBOARD_DIST_DIR):
        paths.append(os.path.join(DASHBOARD_DIST_DIR, 'contamination_risk_zones.geojson'))

    for path in paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"Writing {len(gdf)} hotspots to {path}...")
        gdf.to_file(path, driver='GeoJSON')

def main():
    risk_gdf = calculate_contamination_risk()
    if risk_gdf.empty:
        print("No contamination hotspots found.")
        return

    print("\n--- Saving Results ---")
    write_outputs(risk_gdf)
    print("Analysis complete!")

if __name__ == '__main__':
    main()
