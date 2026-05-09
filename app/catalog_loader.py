import json
from pathlib import Path
from functools import lru_cache
from app.config import settings


@lru_cache(maxsize=1)
def load_clean_catalog():
    path = Path(settings.cleaned_json_path)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    return []


def reload_clean_catalog():
    load_clean_catalog.cache_clear()
    return load_clean_catalog()
