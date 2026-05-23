import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "data" / "karnataka-ground-water-quality-reports"
OUTPUT_FILE = BASE_DIR / "dashboard" / "public" / "Moddata" / "groundwater_quality.geojson"


def parse_number(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_coordinate(value):
    """Parse decimal or simple DMS-like coordinates found in the source CSVs."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        pass

    parts = text.replace(",", " ").split()
    if len(parts) == 3:
        try:
            degrees, minutes, seconds = [float(part) for part in parts]
            return degrees + minutes / 60 + seconds / 3600
        except ValueError:
            return None

    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) >= 4:
        try:
            degrees = float(parts[0])
            minutes = float(parts[1][:2])
            seconds = float(parts[1][2:])
            return degrees + minutes / 60 + seconds / 3600
        except ValueError:
            return None

    if text.count(".") > 1:
        first, rest = text.split(".", 1)
        cleaned = first + "." + rest.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def quality_status(nitrate, fluoride, iron, hardness):
    issues = []

    if nitrate is not None and nitrate > 45:
        issues.append("High nitrate")
    if fluoride is not None and fluoride > 1.5:
        issues.append("High fluoride")
    elif fluoride is not None and fluoride > 1.0:
        issues.append("Elevated fluoride")
    if iron is not None and iron > 0.3:
        issues.append("High iron")
    if hardness is not None and hardness > 600:
        issues.append("Very hard water")
    elif hardness is not None and hardness > 200:
        issues.append("Hard water")

    high_concern = any(
        issue in issues
        for issue in ("High nitrate", "High fluoride", "High iron", "Very hard water")
    )

    if high_concern:
        return "High concern", issues
    if issues:
        return "Caution", issues
    return "Within limits", issues


def row_to_feature(row, source_file):
    latitude = parse_coordinate(row.get("Latitude"))
    longitude = parse_coordinate(row.get("Longitude"))

    if latitude is None or longitude is None:
        return None
    if not (12 <= latitude <= 14 and 77 <= longitude <= 78.5):
        return None

    nitrate = parse_number(row.get("NO3 (mg/L)"))
    fluoride = parse_number(row.get("Flouride (mg/L)") or row.get("Fluoride (mg/L)"))
    iron = parse_number(row.get("Fe mg/L "))
    hardness = parse_number(row.get("TH (as CaCO3) mg/L"))
    status, issues = quality_status(nitrate, fluoride, iron, hardness)

    sample_id = row.get("Well ID") or row.get("ID") or row.get("Well Code") or ""

    return {
        "type": "Feature",
        "properties": {
            "sample_id": sample_id,
            "source_file": source_file,
            "district": row.get("District", ""),
            "taluk": row.get("Taluk", ""),
            "village": row.get("Village", ""),
            "nitrate_mg_l": nitrate,
            "fluoride_mg_l": fluoride,
            "iron_mg_l": iron,
            "hardness_mg_l": hardness,
            "status": status,
            "issues": ", ".join(issues) if issues else "None",
            "remarks": row.get("Remarks", ""),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
    }


def main():
    features = []
    skipped = 0

    for csv_path in sorted(INPUT_DIR.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                feature = row_to_feature(row, csv_path.name)
                if feature is None:
                    skipped += 1
                    continue
                features.append(feature)

    output = {
        "type": "FeatureCollection",
        "name": "groundwater_quality",
        "features": features,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False)

    status_counts = {}
    for feature in features:
        status = feature["properties"]["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"Wrote {len(features)} groundwater quality points to {OUTPUT_FILE}")
    print(f"Skipped {skipped} rows with invalid/out-of-bounds coordinates")
    print(f"Status counts: {status_counts}")


if __name__ == "__main__":
    main()
