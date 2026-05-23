import geopandas as gpd

wards_path = '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata/ward_risk_thematic.geojson'
slums_path = '/Users/bharatoraon/Desktop/Datajam/bengaluru-urban-slums/bbmp_bangalore_slum_boundaries.geojson'

wards = gpd.read_file(wards_path)
slums = gpd.read_file(slums_path)

print(f"Total wards: {len(wards)}, Total slums: {len(slums)}")

if slums.crs != wards.crs:
    slums = slums.to_crs(wards.crs)

# Sjoin: assign each slum to a ward (using centroid to avoid double counting if a slum crosses borders, but intersects is fine for count)
slums['centroid'] = slums.geometry.centroid
slums.set_geometry('centroid', inplace=True)

joined = gpd.sjoin(slums, wards, how="inner", predicate="intersects")
counts = joined.groupby('index_right').size().reset_index(name='slum_count')

print(counts.head())
print(f"Total wards with slums: {len(counts)}")
