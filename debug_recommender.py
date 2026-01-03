from recommender import Recommender
import pandas as pd

try:
    print("Initializing Recommender...")
    rec = Recommender()
    
    print("\n--- Model/Data Info ---")
    print(f"Meta DF Shape: {rec.meta_df.shape}")
    print(f"Meta DF Columns: {rec.meta_df.columns.tolist()}")
    print(f"Recent Items Count: {len(rec.recent_items)}")
    
    print(f"Meta DF Index Dtype: {rec.meta_df.index.dtype}")
    print(f"Meta DF Index Sample: {rec.meta_df.index[:5].tolist()}")
    
    print("\n--- Intersection Check ---")
    # Decode all recent items
    all_recent_indices = rec.recent_items if isinstance(rec.recent_items, list) else []
    if all_recent_indices and isinstance(all_recent_indices[0], (int, np.integer)):
         all_recent_asins = rec.item_encoder.inverse_transform(all_recent_indices)
    else:
         all_recent_asins = all_recent_indices
         
    matching = [a for a in all_recent_asins if a in rec.meta_df.index]
    print(f"Total Recent Items: {len(all_recent_asins)}")
    print(f"Matching Meta Items: {len(matching)}")
    
    print("\n--- Image URL Check ---")
    if matching:
        first_match = rec.meta_df.loc[matching[0]]
        print(f"Image Value: {first_match['image_url']}")
        print(f"Image Type: {type(first_match['image_url'])}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
