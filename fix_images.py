import pandas as pd
import os
import ast

ARTIFACTS_DIR = 'artifacts'
DATA_DIR = 'data'

print("Loading current metadata...")
meta_df = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
# Ensure asin is a column, reset index if it was the index
if 'asin' not in meta_df.columns and meta_df.index.name == 'asin':
    meta_df.reset_index(inplace=True)

print(f"Meta DF shape: {meta_df.shape}")

print("Loading raw image data...")
image_df = pd.read_json(os.path.join(DATA_DIR, "meta_All_Beauty_25.json"), lines=True)
# Keep only relevant columns
image_df = image_df[['asin', 'image']]
print(f"Raw Image DF shape: {image_df.shape}")

# Ensure asin is string
meta_df['asin'] = meta_df['asin'].astype(str)
image_df['asin'] = image_df['asin'].astype(str)

# Handle image column data types (ensure list or None)
def clean_image(val):
    if isinstance(val, list):
        return val
    return None

image_df['image'] = image_df['image'].apply(clean_image)

# Drop duplicates in image_df
image_df.drop_duplicates(subset=['asin'], inplace=True)
print(f"Deduped Image DF shape: {image_df.shape}")

print("Merging data...")
# Use left join
merged_df = pd.merge(meta_df, image_df, on='asin', how='left')
print(f"Merged DF shape: {merged_df.shape}")

print("Renaming column...")
merged_df.rename(columns={'image': 'image_url'}, inplace=True)

# Fill NaN with empty list or None if preferred? 
# Recommender expects list or None. Parquet handles nulls.

# Check if image_url exists
if 'image_url' in merged_df.columns:
    print("Column 'image_url' created successfully.")
    non_null_count = merged_df['image_url'].notnull().sum()
    print(f"Rows with images: {non_null_count} out of {len(merged_df)}")
    
    if non_null_count == 0:
        print("DEBUG: ASIN Mismatch Investigation")
        print(f"Sample Meta ASINs: {meta_df['asin'].head().tolist()}")
        print(f"Sample Image ASINs: {image_df['asin'].head().tolist()}")
        # Check intersection
        common = set(meta_df['asin']).intersection(set(image_df['asin']))
        print(f"Common ASINs count: {len(common)}")
else:
    print("CRITICAL: image_url column missing after merge/rename!")

print("Saving updated artifacts...")
merged_df.to_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
print("Done!")
