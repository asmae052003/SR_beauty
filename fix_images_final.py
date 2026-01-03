import pandas as pd
import os
import json

ARTIFACTS_DIR = 'artifacts'
DATA_DIR = 'data'

print("Loading metadata...")
meta_df = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
if 'asin' not in meta_df.columns:
    meta_df.reset_index(inplace=True)

# Aggressive clean of ASINs
meta_df['asin'] = meta_df['asin'].astype(str).str.strip()
print(f"Meta entries: {len(meta_df)}")

print("Loading json data...")
# Read as standard JSON array using pandas (as per data.ipynb findings)
try:
    image_df = pd.read_json(os.path.join(DATA_DIR, "meta_All_Beauty_25.json"))
except ValueError:
    print("Pandas read_json failed. Fallback to json.load")
    with open(os.path.join(DATA_DIR, "meta_All_Beauty_25.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    image_df = pd.DataFrame(data)

print(f"Loaded {len(image_df)} raw metadata entries.")

# Filter and Extract Images
if 'image' in image_df.columns:
    # Filter rows where image is a non-empty list
    mask = image_df['image'].apply(lambda x: isinstance(x, list) and len(x) > 0)
    image_df = image_df[mask].copy()
    
    # Extract first URL
    image_df['image_url'] = image_df['image'].apply(lambda x: x[0] if x else None)
    
    # Keep subset
    image_df = image_df[['asin', 'image_url']]
    
    # Clean ASINs
    image_df['asin'] = image_df['asin'].astype(str).str.strip()
    image_df.drop_duplicates(subset=['asin'], inplace=True)
    
    print(f"Extracted {len(image_df)} items with valid images.")
else:
    print("CRITICAL: 'image' column missing in loaded JSON.")
    exit(1)

print("Merging...")
# Drop existing image_url from meta_df if it exists (from previous partial runs)
if 'image_url' in meta_df.columns:
    print("Dropping old image_url column from metadata...")
    meta_df.drop(columns=['image_url'], inplace=True)

# Merge strictly on ASIN
merged_df = pd.merge(meta_df, image_df, on='asin', how='left')

# Check results
found = merged_df['image_url'].notnull().sum()
print(f"Merged successfully. Items with images: {found}")

# Validate if we actually recovered images for known items
if found == 0:
    print("WARNING: Zero matches found. Verification needed.")
else:
    print("Success: Images recovered.")

print("Saving...")
merged_df.to_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
print("Done!")
