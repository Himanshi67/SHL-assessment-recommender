# """Placeholder: build a simple inverted index for quick retrieval."""
# import sys
# sys.path.insert(0, '..')
# import json
# from pathlib import Path
# from collections import defaultdict
# from app.config import settings
# # from app.catalog_loader import load_raw_catalog, clean_catalog

# # raw = load_raw_catalog()
# # cleaned = clean_catalog(raw)

# index = defaultdict(list)
# for it in cleaned:
#     text = ' '.join([it.get('name',''), it.get('description','')] + it.get('keys',[]))
#     for tok in set(word.lower() for word in text.split() if len(word) > 2):
#         index[tok].append(it.get('entity_id'))

# out = Path('data/processed/inverted_index.json')
# out.parent.mkdir(parents=True, exist_ok=True)
# with open(out, 'w', encoding='utf-8') as f:
#     json.dump(index, f, indent=2)
# print('Built inverted index with', len(index), 'tokens')
