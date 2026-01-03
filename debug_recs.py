from recommender import Recommender
import numpy as np

def debug():
    rec = Recommender()
    encoder = rec.item_encoder
    encoder_items = set(encoder.classes_)
    
    # Find items in meta NOT in encoder (Cold items)
    cold_candidates = [asin for asin in rec.meta_df.index if asin not in encoder_items]
    print(f"Found {len(cold_candidates)} cold items (out of {len(rec.meta_df)} total).")
    
    if len(cold_candidates) < 3:
        print("Not enough cold items to test fallback.")
        return

    # Scenario 3: Cold Items Fallback
    test_asins_cold = cold_candidates[:3]
    print(f"\n--- Test Case 3: Cold Inputs {test_asins_cold} ---")
    # Verify titles/categories
    for asin in test_asins_cold:
        cat = rec.meta_df.loc[asin, 'main_cat']
        print(f"  Input: {asin} - Cat: {cat}")

    recs_cold = rec.recommend_from_history(test_asins_cold, k=5)
    print("Recommendations:")
    for r in recs_cold:
        print(f"  {r['asin']} - {r['title']} (Cat: {r.get('main_cat')})")

if __name__ == "__main__":
    debug()

if __name__ == "__main__":
    debug()
