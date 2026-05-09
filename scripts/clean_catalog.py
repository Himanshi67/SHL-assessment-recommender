import json
from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw/shl_product_catalog.json")
CLEAN_JSON_PATH = Path("data/processed/shl_catalog_clean.json")
CLEAN_CSV_PATH = Path("data/processed/shl_catalog_clean.csv")


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if v is not None)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def load_raw_data():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("products", []) or data.get("data", []) or [data]
    return []


def derive_test_type(keys):
    text = safe_text(keys).lower()

    if "knowledge & skills" in text:
        return "Knowledge & Skills"
    if "personality & behavior" in text:
        return "Personality & Behavior"
    if "ability & aptitude" in text:
        return "Ability & Aptitude"
    if "assessment exercises" in text:
        return "Assessment Exercises"

    return "General"


def normalize_record(item):
    return {
        "entity_id": safe_text(item.get("entity_id")),
        "name": safe_text(item.get("name")),
        "url": safe_text(item.get("link")),
        "description": safe_text(item.get("description")),
        "tags": safe_text(item.get("keys")),
        "test_type": derive_test_type(item.get("keys")),
        "remote_testing": safe_text(item.get("remote")),
        "adaptive_irt": safe_text(item.get("adaptive")),
        "duration": safe_text(item.get("duration")),
        "job_levels": safe_text(item.get("job_levels")),
        "languages": safe_text(item.get("languages")),
        "status": safe_text(item.get("status")),
        "scraped_at": safe_text(item.get("scraped_at")),
    }   


def main():
    if not RAW_PATH.exists():
        print(f"Missing raw file: {RAW_PATH}")
        return

    records = load_raw_data()
    print(f"Loaded raw records: {len(records)}")

    cleaned = [normalize_record(item) for item in records if isinstance(item, dict)]
    df = pd.DataFrame(cleaned)

    df["name"] = df["name"].fillna("").str.strip()
    df["url"] = df["url"].fillna("").str.strip()
    df["description"] = df["description"].fillna("").str.strip()

    df = df[(df["name"] != "") & (df["url"] != "")]
    df = df.drop_duplicates(subset=["name", "url"]).reset_index(drop=True)

    CLEAN_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(CLEAN_JSON_PATH, orient="records", indent=2, force_ascii=False)
    df.to_csv(CLEAN_CSV_PATH, index=False)

    print(f"\nCleaned rows saved: {len(df)}")
    print(f"JSON saved to: {CLEAN_JSON_PATH}")
    print(f"CSV saved to: {CLEAN_CSV_PATH}")

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nSample rows:")
    print(df.head(3).to_dict(orient="records"))


if __name__ == "__main__":
    main()
