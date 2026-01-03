import pandas as pd
import os

ARTIFACTS_DIR = 'artifacts'
DATA_DIR = 'data'

print("Loading metadata...")
meta_df = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
# Ensure asin is string
if 'asin' not in meta_df.columns:
    meta_df.reset_index(inplace=True)
meta_df['asin'] = meta_df['asin'].astype(str)

print("Loading reviews data...")
# Read columns 'asin', 'image' from reviews
reviews_df = pd.read_json(os.path.join(DATA_DIR, "All_Beauty_25.json"), lines=True)
reviews_df = reviews_df[['asin', 'image']]

# Filter for rows that actually have images
reviews_with_imgs = reviews_df[reviews_df['image'].notnull()].copy()
print(f"Reviews with images: {len(reviews_with_imgs)}")

# Ensure asin is string
reviews_with_imgs['asin'] = reviews_with_imgs['asin'].astype(str)

# Clean images (take first one)
def get_first_image(val):
    if isinstance(val, list) and len(val) > 0:
        return val[0]
    return None

reviews_with_imgs['image_url'] = reviews_with_imgs['image'].apply(get_first_image)
reviews_with_imgs = reviews_with_imgs[['asin', 'image_url']].drop_duplicates(subset=['asin'])

print("Merging...")
merged_df = pd.merge(meta_df, reviews_with_imgs, on='asin', how='left')

# Coalesce if validation fails
if 'image_url_x' in merged_df.columns:
    merged_df['image_url'] = merged_df['image_url_x'].combine_first(merged_df['image_url_y'])
    merged_df.drop(columns=['image_url_x', 'image_url_y'], inplace=True)

print(f"Non-null images: {merged_df['image_url'].notnull().sum()}")

print("Saving...")
merged_df.to_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
print("Done!")
