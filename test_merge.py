import pandas as pd
import geopandas as gpd

csv_path = '/Users/bharatoraon/Desktop/Datajam/gba-wards-delimitation-2025/6ad468a8-b1b5-45dd-8a54-7e53123e56f9.csv'
gdf_path = '/Users/bharatoraon/Desktop/Datajam/dashboard/public/Moddata/ward_risk_thematic.geojson'

df = pd.read_csv(csv_path)
gdf = gpd.read_file(gdf_path)

# Extract Ward_No from Ward_No_Name in CSV
df['ward_no'] = df['Ward_No_Name'].str.split('-').str[0].str.strip()

# We already have 'ward_id' in gdf (e.g. "5")
print("GDF ward_ids:", gdf['ward_id'].unique()[:10])
print("CSV ward_nos:", df['ward_no'].unique()[:10])

merged = gdf.merge(df, left_on='ward_id', right_on='ward_no', how='left')
missing = merged['TOT_P'].isna().sum()

print(f"Total wards: {len(gdf)}. Successfully merged: {len(gdf) - missing}. Missing: {missing}")
