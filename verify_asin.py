import pandas as pd
import os

ARTIFACTS_DIR = 'artifacts'
DATA_DIR = 'data'

print("--- Metadata Parquet ---")
meta = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
if 'asin' in meta.columns:
    print(f"ASIN column exists. Type: {meta['asin'].dtype}")
    print(meta['asin'].head().values)
else:
    print("ASIN column MISSING. Index name:", meta.index.name)
    print(meta.index[:5])

print("\n--- JSON Data ---")
json_df = pd.read_json(os.path.join(DATA_DIR, "meta_All_Beauty_25.json"), lines=True, chunksize=5)
for chunk in json_df:
    print(f"ASIN column exists. Type: {chunk['asin'].dtype}")
    print(chunk['asin'].values)
    break
