from recommender import Recommender

rec = Recommender()
encoder_items = set(rec.item_encoder.classes_)

# Items clicked by browser agent (titles from log, I need ASINs ideally, but I'll search by title in metadata to be sure)
# Or I can just check general stats.

print(f"Total items in Metadata: {len(rec.meta_df)}")
print(f"Total items in Encoder: {len(encoder_items)}")

intersect = len(set(rec.meta_df.index).intersection(encoder_items))
print(f"Intersection: {intersect}")

# Check specific items if possible.
# I'll just check a sample from metadata and see if they are in encoder.
sample = rec.meta_df.index[:5]
for asin in sample:
    print(f"ASIN {asin} in encoder? {asin in encoder_items}")
