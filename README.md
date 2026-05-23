# Water Quality Infrastructure Analysis

This folder is a Bengaluru water-quality data pipeline. It downloads public datasets, then calculates drain/sewage contamination hotspots using infrastructure overlap, field observations, sensitive receptors, and drain-edge typology.

## Core Workflow

1. Download the source datasets listed in `urls.txt` into `data/`.
2. Load BWSSB sewerage, manholes, water-supply assets, stormwater drains, drain typology, field audits, lakes, wetlands, and optional slum polygons.
3. Reproject to UTM Zone 43N so distances are measured in meters.
4. Score each drain segment using sewage proximity/overlap, nearby manholes, audit evidence, typology exposure, water-supply proximity, receptor proximity, and slum proximity when that layer exists.
5. Convert scored drain candidates into hotspot points for the dashboard heatmap and popup layer.
6. Write the result to `contamination_risk_zones.geojson` and `dashboard/public/contamination_risk_zones.geojson`.

## Contamination Risk Scoring

The current score is a 0-100 composite:

- Sewage/drain overlap or proximity is the main hazard signal: within 5 m scores highest, with smaller scores out to 30 m.
- Manholes near drains add supporting contamination risk out to 30 m.
- Citizen audits add field evidence when reports include black/grey water, oily films, foam, unauthorised inlets, stagnant water, or smell.
- Typology uses the `typ` field from `mod-foundation_typology_analysis.geojson`. Property-adjacent drains (`t4`, `t5`, `t8`) and lake-adjacent drains (`t6`, `t7`) score higher than roads, open space, agricultural land, or vacant land.
- Existing lakes and wetlands add receptor pressure within 100 m.
- Water-supply assets add public-health exposure pressure within 30 m.
- Slum proximity is supported if a `slums.geojson` layer is added to one of the `Moddata` folders. No slum polygon layer is currently present in this checkout.

## Commands

Create or reuse a Python environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Download only the core datasets needed for the contamination-risk analysis:

```bash
python -u download_data.py --only \
  bwssb-water-supply-lines-map-of-bengaluru \
  bwssb-sewerage-line-maps-for-bengaluru \
  bwssb-manholes-in-bengaluru
```

Run the risk analysis:

```bash
python -u analyze_infrastructure.py
```

Export measured groundwater quality samples for the dashboard overlay:

```bash
python -u export_groundwater_quality.py
```

Export the latest monthly lake water-quality report from the downloaded PDFs:

```bash
python -u export_lake_water_quality.py
```

Export Bengaluru land-slope classes for the natural-drainage dashboard overlay:

```bash
python -u export_slopes.py
```

Run the dashboard:

```bash
cd dashboard
npm install
npm run dev
```

## Notes

- `download_data.py` can still process all URLs in `urls.txt`, but that downloads many large planning, hydrology, budget, and civic datasets under `data/`.
- `analyze_infrastructure.py` includes a fallback XML KML parser because some OpenCity KMLs fail in GeoPandas/GDAL even though their coordinate data is usable. If raw downloads are unavailable, it falls back to exported GeoJSONs in `dashboard/public/Moddata` and `dashboard/dist/Moddata`.
- `export_groundwater_quality.py` converts `data/karnataka-ground-water-quality-reports/*.csv` into `dashboard/public/Moddata/groundwater_quality.geojson`.
- `export_lake_water_quality.py` scans `data/bengaluru-lake-monthly-water-quality-reports/*.pdf`, selects the latest report month, extracts table rows, scores pollution levels, and joins matched rows to lake geometries in `dashboard/public/Moddata/lake_water_quality.geojson`.
- `export_slopes.py` converts `data/bengaluru-slopes/*.kml` into `dashboard/public/Moddata/bengaluru_slopes.geojson` for comparing SWDs against terrain slope classes.
- The dashboard includes natural drainage context layers for valley systems, watershed/sub-basin boundaries, stream order, and land slopes.
- `export_raw.py`, `simplify_geojson.py`, and `process_audits.py` appear to be dashboard-preparation helpers. `process_audits.py` expects a local `data/Moddata/mod-foundation_form-2.csv` file that is not included here.
