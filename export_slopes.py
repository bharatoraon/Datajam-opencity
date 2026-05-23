import json
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "bengaluru-slopes" / "1cc93f37-13b8-4a6e-893e-ae8df9b673ba.kml"
OUTPUT_FILE = BASE_DIR / "dashboard" / "public" / "Moddata" / "bengaluru_slopes.geojson"
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def clean_text(value):
    return " ".join(str(value or "").split())


def parse_coordinates(text):
    coordinates = []
    for item in clean_text(text).split():
        parts = item.split(",")
        if len(parts) < 2:
            continue
        try:
            coordinates.append([float(parts[0]), float(parts[1])])
        except ValueError:
            continue
    return coordinates


def placemark_properties(placemark):
    properties = {}
    for item in placemark.findall(".//kml:SimpleData", KML_NS):
        key = item.attrib.get("name")
        if key:
            properties[key] = clean_text(item.text)
    return properties


def placemark_geometry(placemark):
    polygons = []
    for polygon in placemark.findall(".//kml:Polygon", KML_NS):
        outer = polygon.find(".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", KML_NS)
        if outer is None:
            continue
        exterior = parse_coordinates(outer.text)
        if len(exterior) < 4:
            continue

        rings = [exterior]
        for inner in polygon.findall(".//kml:innerBoundaryIs/kml:LinearRing/kml:coordinates", KML_NS):
            interior = parse_coordinates(inner.text)
            if len(interior) >= 4:
                rings.append(interior)
        polygons.append(rings)

    if not polygons:
        return None
    if len(polygons) == 1:
        return {"type": "Polygon", "coordinates": polygons[0]}
    return {"type": "MultiPolygon", "coordinates": polygons}


def main():
    root = ET.parse(INPUT_FILE).getroot()
    features = []

    for placemark in root.findall(".//kml:Placemark", KML_NS):
        geometry = placemark_geometry(placemark)
        if geometry is None:
            continue

        properties = placemark_properties(placemark)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "slope": properties.get("SLOPE", ""),
                    "description": properties.get("DESCRIPTIO", ""),
                    "slope_code": properties.get("SLP_CODE", ""),
                    "source_area": properties.get("NR.DBO.Slope.AREA", ""),
                },
                "geometry": geometry,
            }
        )

    output = {
        "type": "FeatureCollection",
        "name": "bengaluru_slopes",
        "features": features,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")

    counts = {}
    for feature in features:
        slope = feature["properties"]["slope"]
        counts[slope] = counts.get(slope, 0) + 1

    print(f"Wrote {len(features)} slope polygons to {OUTPUT_FILE}")
    print(f"Slope classes: {counts}")


if __name__ == "__main__":
    main()
