import json
from pathlib import Path

RAW_PATH = Path("data/raw/shl_product_catalog.json")


def summarize_value(value, max_len=120):
    if isinstance(value, dict):
        return f"dict(keys={list(value.keys())[:10]})"
    if isinstance(value, list):
        preview = value[:2]
        return f"list(len={len(value)}, sample={preview})"
    text = str(value)
    return text[:max_len]


def main():
    if not RAW_PATH.exists():
        print(f"File not found: {RAW_PATH}")
        return

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 80)
    print("TOP LEVEL TYPE:", type(data).__name__)
    print("=" * 80)

    if isinstance(data, dict):
        print("Top-level keys:")
        for key in data.keys():
            print("-", key)

        print("\nTop-level preview:")
        for key, value in list(data.items())[:10]:
            print(f"{key}: {summarize_value(value)}")

        # Try to detect main record list
        candidate_lists = {k: v for k, v in data.items() if isinstance(v, list)}
        if candidate_lists:
            print("\nPossible record lists found:")
            for key, value in candidate_lists.items():
                print(f"- {key}: {len(value)} items")

            first_key = next(iter(candidate_lists))
            records = candidate_lists[first_key]
        else:
            records = [data]

    elif isinstance(data, list):
        print(f"Total records: {len(data)}")
        records = data
    else:
        print("Unsupported JSON structure")
        return

    if not records:
        print("\nNo records found.")
        return

    first = records[0]
    print("\n" + "=" * 80)
    print("FIRST RECORD TYPE:", type(first).__name__)
    print("=" * 80)

    if isinstance(first, dict):
        print("Fields in first record:")
        for key in first.keys():
            print("-", key)

        print("\nFirst record sample values:")
        for key, value in first.items():
            print(f"{key}: {summarize_value(value)}")

        print("\nField frequency across first 20 records:")
        field_counts = {}
        for item in records[:20]:
            if isinstance(item, dict):
                for key in item.keys():
                    field_counts[key] = field_counts.get(key, 0) + 1

        for key, count in sorted(field_counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"{key}: present in {count}/20")
    else:
        print("First record is not a dictionary:", first)


if __name__ == "__main__":
    main()
