import json
import logging
import re
import warnings
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path

import pdfplumber


logging.getLogger("pdfminer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message="CropBox missing from /Page.*")

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "data" / "bengaluru-lake-monthly-water-quality-reports"
MODDATA_DIR = BASE_DIR / "dashboard" / "public" / "Moddata"
OUTPUT_FILE = MODDATA_DIR / "lake_water_quality.geojson"
UNMATCHED_FILE = MODDATA_DIR / "lake_water_quality_unmatched.json"
LAKE_GEOMETRY_FILES = [
    MODDATA_DIR / "mod-foundation_lakes_existing.geojson",
    MODDATA_DIR / "mod-foundation_lakes_lost.geojson",
]

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

COLUMNS = [
    "stn_code",
    "sampling_month",
    "monitoring_location",
    "use_based_class",
    "temperature_c",
    "dissolved_oxygen_mg_l",
    "ph",
    "conductivity_umho_cm",
    "bod_mg_l",
    "nitrate_n_mg_l",
    "nitrite_n_mg_l",
    "fecal_coliform_mpn_100ml",
    "total_coliform_mpn_100ml",
    "carbonate_mg_l",
    "bicarbonate_mg_l",
    "turbidity_ntu",
    "phenolphthalein_alkalinity_mg_l",
    "total_alkalinity_mg_l",
    "chlorides_mg_l",
    "cod_mg_l",
    "total_kjeldahl_nitrogen_mg_l",
    "ammonical_n_mg_l",
    "total_hardness_mg_l",
    "calcium_as_caco3_mg_l",
    "calcium_mg_l",
    "magnesium_as_caco3_mg_l",
    "magnesium_mg_l",
    "sulphate_mg_l",
    "sodium_mg_l",
    "total_dissolved_solids_mg_l",
    "total_suspended_solids_mg_l",
    "phosphate_mg_l",
    "boron_mg_l",
    "potassium_mg_l",
    "fluoride_mg_l",
    "sodium_percentage",
    "sar",
    "ortho_phosphate_mg_l",
]


def clean_text(value):
    return " ".join(str(value or "").replace("\n", " ").split())


def parse_number(value):
    text = clean_text(value)
    if not text:
        return None
    if text.upper() == "BDL":
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0))


def infer_report_month(pdf_path):
    candidates = []
    search_texts = [pdf_path.stem.replace("_", " ").replace("-", " ")]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page_text = pdf.pages[0].extract_text() or ""
            search_texts.insert(0, first_page_text)
    except Exception as error:
        print(f"Could not read {pdf_path.name} while inferring month: {error}")

    month_pattern = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))
    for text in search_texts:
        normalized = clean_text(text).lower()
        for match in re.finditer(rf"\b({month_pattern})\b\s*[- ]*\s*(20\d{{2}}|\d{{2}})?", normalized):
            month = MONTHS[match.group(1)]
            year_text = match.group(2)
            if not year_text:
                continue
            year = int(year_text)
            if year < 100:
                year += 2000
            candidates.append((year, month))

    if candidates:
        return max(candidates)
    return None


def latest_pdf():
    reports = []
    for pdf_path in sorted(INPUT_DIR.glob("*.pdf")):
        inferred = infer_report_month(pdf_path)
        if inferred:
            reports.append((inferred[0], inferred[1], pdf_path))

    if not reports:
        raise RuntimeError(f"No monthly lake water-quality reports found in {INPUT_DIR}")

    reports.sort()
    return reports[-1]


def is_data_table(table):
    if not table or len(table) < 2:
        return False
    header = table[0]
    if len(header) < 20:
        return False
    return "stn" in clean_text(header[0]).lower()


def extract_latest_rows(pdf_path, report_year, report_month):
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not is_data_table(table):
                    continue
                for row in table[1:]:
                    row = list(row or [])
                    if len(row) < 10 or not clean_text(row[0]).isdigit():
                        continue
                    row = row[: len(COLUMNS)] + [None] * max(0, len(COLUMNS) - len(row))
                    raw_record = dict(zip(COLUMNS, row))
                    records.append(normalize_record(raw_record, pdf_path.name, report_year, report_month))
    return records


def normalize_record(raw_record, source_pdf, report_year, report_month):
    record = {
        "source_pdf": source_pdf,
        "report_year": report_year,
        "report_month": report_month,
        "report_month_name": MONTH_NAMES[report_month],
    }

    for key, value in raw_record.items():
        if key in {
            "stn_code",
            "sampling_month",
            "monitoring_location",
            "use_based_class",
        }:
            record[key] = clean_text(value)
        else:
            record[key] = parse_number(value)

    level, score, drivers = pollution_level(record)
    record["pollution_level"] = level
    record["pollution_score"] = score
    record["pollution_drivers"] = ", ".join(drivers) if drivers else "None"
    return record


def add_driver(drivers, label, value, severe=None, moderate=None, low_is_bad=False):
    if value is None:
        return 0

    if low_is_bad:
        if severe is not None and value < severe:
            drivers.append(f"{label} {value:g}")
            return 3
        if moderate is not None and value < moderate:
            drivers.append(f"{label} {value:g}")
            return 1
        return 0

    if severe is not None and value > severe:
        drivers.append(f"{label} {value:g}")
        return 3
    if moderate is not None and value > moderate:
        drivers.append(f"{label} {value:g}")
        return 1
    return 0


def pollution_level(record):
    drivers = []
    score = 0

    score += add_driver(drivers, "low DO", record.get("dissolved_oxygen_mg_l"), severe=4, moderate=5, low_is_bad=True)
    score += add_driver(drivers, "high BOD", record.get("bod_mg_l"), severe=10, moderate=3)
    score += add_driver(drivers, "high COD", record.get("cod_mg_l"), severe=50, moderate=25)
    score += add_driver(drivers, "high fecal coliform", record.get("fecal_coliform_mpn_100ml"), severe=2500, moderate=500)
    score += add_driver(drivers, "high total coliform", record.get("total_coliform_mpn_100ml"), severe=5000, moderate=2500)
    score += add_driver(drivers, "high turbidity", record.get("turbidity_ntu"), severe=50, moderate=10)
    score += add_driver(drivers, "high ammonia-N", record.get("ammonical_n_mg_l"), severe=1.2, moderate=0.5)
    score += add_driver(drivers, "high nitrate-N", record.get("nitrate_n_mg_l"), severe=10, moderate=5)
    score += add_driver(drivers, "high TDS", record.get("total_dissolved_solids_mg_l"), severe=1000, moderate=500)

    ph = record.get("ph")
    if ph is not None:
        if ph < 6 or ph > 9:
            drivers.append(f"pH {ph:g}")
            score += 3
        elif ph < 6.5 or ph > 8.5:
            drivers.append(f"pH {ph:g}")
            score += 1

    if score >= 9:
        return "Severe", score, drivers
    if score >= 5:
        return "High", score, drivers
    if score >= 1:
        return "Moderate", score, drivers
    return "Low", score, drivers


def normalize_lake_name(name):
    text = clean_text(name).lower()
    text = re.sub(r"â", "", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)

    stopwords = {
        "lake",
        "tank",
        "kere",
        "kerey",
        "training",
        "centre",
        "center",
        "temple",
        "of",
        "fish",
        "breeding",
        "near",
        "nearby",
        "by",
        "road",
        "main",
        "bengaluru",
        "bengalore",
        "bangalore",
        "taluka",
        "east",
        "west",
        "north",
        "south",
        "village",
        "vill",
        "at",
    }
    tokens = []
    for token in text.split():
        if token in stopwords:
            continue
        tokens.append(token)
    return " ".join(tokens)


def load_lake_geometries():
    lake_features = []
    for path in LAKE_GEOMETRY_FILES:
        data = json.loads(path.read_text())
        geometry_group = "existing" if "existing" in path.name else "lost"
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            name = clean_text(props.get("name"))
            if not name:
                continue
            lake_features.append(
                {
                    "name": name,
                    "normalized_name": normalize_lake_name(name),
                    "geometry_group": geometry_group,
                    "geometry": feature.get("geometry"),
                    "source_properties": props,
                }
            )
    return lake_features


def match_lake(record, lake_features):
    target = normalize_lake_name(record["monitoring_location"])
    if not target:
        return None, 0

    best = None
    best_score = 0
    target_tokens = set(target.split())

    for lake in lake_features:
        candidate = lake["normalized_name"]
        if not candidate:
            continue
        candidate_tokens = set(candidate.split())
        ratio = SequenceMatcher(None, target, candidate).ratio()
        overlap = 0
        if target_tokens and candidate_tokens:
            overlap = len(target_tokens & candidate_tokens) / len(target_tokens | candidate_tokens)

        # Prefer exact lake-name token matches over longer names that only contain
        # the token, e.g. "Bellandur Lake" should match "Bellandur Amanikere"
        # before "Chikkabellanduru kere".
        if target_tokens == candidate_tokens:
            score = 1.2
        elif target_tokens and target_tokens.issubset(candidate_tokens):
            score = 1.1 - (0.01 * (len(candidate_tokens) - len(target_tokens)))
        elif candidate_tokens and candidate_tokens.issubset(target_tokens):
            score = 1.0 - (0.01 * (len(target_tokens) - len(candidate_tokens)))
        else:
            contains_bonus = 0.08 if target in candidate or candidate in target else 0
            score = max(ratio, overlap) + contains_bonus

        if score > best_score:
            best = lake
            best_score = score

    if best_score < 0.72:
        return None, best_score
    return best, best_score


def build_geojson(records):
    lake_features = load_lake_geometries()
    by_lake = {}
    unmatched = []

    for record in records:
        match, match_score = match_lake(record, lake_features)
        if not match:
            unmatched.append(
                {
                    "stn_code": record["stn_code"],
                    "monitoring_location": record["monitoring_location"],
                    "pollution_level": record["pollution_level"],
                    "pollution_score": record["pollution_score"],
                    "match_score": round(match_score, 3),
                }
            )
            continue

        key = (match["geometry_group"], match["name"])
        current = by_lake.get(key)
        if current is None or record["pollution_score"] > current["record"]["pollution_score"]:
            by_lake[key] = {
                "match": match,
                "record": record,
                "sample_count": 1 if current is None else current["sample_count"] + 1,
                "locations": [record["monitoring_location"]] if current is None else current["locations"] + [record["monitoring_location"]],
                "match_score": match_score,
            }
        else:
            current["sample_count"] += 1
            current["locations"].append(record["monitoring_location"])

    features = []
    for item in by_lake.values():
        match = item["match"]
        record = item["record"]
        props = deepcopy(record)
        props.update(
            {
                "matched_lake_name": match["name"],
                "geometry_group": match["geometry_group"],
                "match_score": round(item["match_score"], 3),
                "sample_count": item["sample_count"],
                "monitoring_locations": "; ".join(sorted(set(item["locations"]))),
                "area_acres": match["source_properties"].get("area_acres"),
                "ward_name": match["source_properties"].get("ward_name"),
                "corporation": match["source_properties"].get("Corporation"),
            }
        )
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": match["geometry"],
            }
        )

    return {
        "type": "FeatureCollection",
        "name": "lake_water_quality",
        "features": features,
    }, unmatched


def main():
    report_year, report_month, pdf_path = latest_pdf()
    records = extract_latest_rows(pdf_path, report_year, report_month)
    geojson, unmatched = build_geojson(records)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    UNMATCHED_FILE.write_text(json.dumps(unmatched, indent=2, ensure_ascii=False), encoding="utf-8")

    level_counts = {}
    for feature in geojson["features"]:
        level = feature["properties"]["pollution_level"]
        level_counts[level] = level_counts.get(level, 0) + 1

    print(f"Selected latest lake report: {MONTH_NAMES[report_month]} {report_year} ({pdf_path.name})")
    print(f"Extracted {len(records)} monitoring rows")
    print(f"Wrote {len(geojson['features'])} matched lake overlays to {OUTPUT_FILE}")
    print(f"Wrote {len(unmatched)} unmatched monitoring rows to {UNMATCHED_FILE}")
    print(f"Pollution level counts: {level_counts}")


if __name__ == "__main__":
    main()
