import os
import pandas as pd
import geopandas as gpd

def main():
    base_dir = '/Users/bharatoraon/Desktop/Datajam'
    risk_points_path = os.path.join(base_dir, 'contamination_risk_zones.geojson')
    wards_path = os.path.join(base_dir, 'Moddata', 'mod-foundation_gba_wards.geojson')
    out_path = os.path.join(base_dir, 'dashboard', 'public', 'Moddata', 'ward_risk_thematic.geojson')

    print("Loading risk points...")
    try:
        points = gpd.read_file(risk_points_path)
    except Exception as e:
        print(f"Error loading points: {e}")
        return

    print("Loading wards boundaries...")
    try:
        wards = gpd.read_file(wards_path)
    except Exception as e:
        print(f"Error loading wards: {e}")
        return

    # Ensure same CRS
    if points.crs != wards.crs:
        points = points.to_crs(wards.crs)

    print("Performing spatial join...")
    # Join points to wards
    joined = gpd.sjoin(points, wards, how="inner", predicate="intersects")
    
    # Count occurrences per ward.
    counts = joined.groupby('index_right').size().reset_index(name='risk_count')

    print("Merging risk counts back to wards...")
    # Merge back to wards GeoDataFrame
    wards['risk_count'] = 0 # default to 0
    wards.loc[counts['index_right'], 'risk_count'] = counts['risk_count'].values

    print("Calculating slum counts per ward...")
    slums_path = os.path.join(base_dir, 'bengaluru-urban-slums', 'bbmp_bangalore_slum_boundaries.geojson')
    try:
        slums = gpd.read_file(slums_path)
        if slums.crs != wards.crs:
            slums = slums.to_crs(wards.crs)
        # Use centroid so we don't double count slums that touch multiple wards, mostly
        slums['geometry'] = slums.geometry.centroid
        
        slum_joined = gpd.sjoin(slums, wards, how="inner", predicate="intersects")
        slum_counts = slum_joined.groupby('index_right').size().reset_index(name='slum_count')
        
        wards['slum_count'] = 0
        wards.loc[slum_counts['index_right'], 'slum_count'] = slum_counts['slum_count'].values
    except Exception as e:
        print(f"Error processing slums: {e}")
        wards['slum_count'] = 0

    # Clean up any potential missing values and ensure it's int
    wards['risk_count'] = wards['risk_count'].fillna(0).astype(int)

    print("Merging socioeconomic data...")
    csv_path = os.path.join(base_dir, 'gba-wards-delimitation-2025', '6ad468a8-b1b5-45dd-8a54-7e53123e56f9.csv')
    try:
        df = pd.read_csv(csv_path)
        # Extract Ward_No
        df['ward_no'] = df['Ward_No_Name'].astype(str).str.split('-').str[0].str.strip()
        
        # Merge key fields: TOT_P, SC_Percent, ST_Percent
        # Using left merge to preserve all wards
        df_sub = df[['ward_no', 'TOT_P', 'SC_Percent', 'ST_Percent']]
        wards = wards.merge(df_sub, left_on='ward_id', right_on='ward_no', how='left')
        
        # Fill missing with 0 or N/A logic if needed, leaving as is for now
    except Exception as e:
        print(f"Error merging socioeconomic data: {e}")
        
    print(f"Saving to {out_path}...")
    wards.to_file(out_path, driver='GeoJSON')
    
    print("Generating ward rankings...")
    import json
    rankings = wards.groupby('ward_name').agg({
        'risk_count': 'sum',
        'slum_count': 'sum'
    }).reset_index()
    
    rankings = rankings.sort_values(by='risk_count', ascending=False)
    top_rankings = rankings.head(100).to_dict(orient='records')
    
    rankings_path = os.path.join(base_dir, 'dashboard', 'public', 'Moddata', 'ward_rankings.json')
    with open(rankings_path, 'w') as f:
        json.dump(top_rankings, f, indent=2)

    print("Done! Ward thematic map data generated with socioeconomic info and rankings.")

if __name__ == '__main__':
    main()
