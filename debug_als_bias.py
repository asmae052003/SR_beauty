from recommender import Recommender
import numpy as np
from sklearn.preprocessing import normalize

def debug_bias():
    rec = Recommender()
    encoder = rec.item_encoder
    # Get all item factors
    factors = rec.als_model.item_factors
    
    # 1. Check Norms
    norms = np.linalg.norm(factors, axis=1)
    print(f"Vector Norms: Min={norms.min():.4f}, Max={norms.max():.4f}, Mean={norms.mean():.4f}")
    
    # Top 5 items with highest norms
    top_norm_indices = np.argsort(norms)[::-1][:5]
    print("\nItems with Highest Norms:")
    for idx in top_norm_indices:
        asin = encoder.inverse_transform([idx])[0]
        meta = rec.meta_df.loc[asin] if asin in rec.meta_df.index else {}
        title = meta.get('title', 'Unknown')
        print(f"  ASIN: {asin} | Norm: {norms[idx]:.4f} | Title: {title}")

    # 2. Test Recommendation Overlap for distinct inputs
    # Pick 2 distinct valid items (middle of norm distribution to be fair)
    mid_indices = np.argsort(norms)[len(norms)//2 : len(norms)//2 + 2]
    asins_input = encoder.inverse_transform(mid_indices)
    
    print(f"\nComparing Recs for Item A ({asins_input[0]}) vs Item B ({asins_input[1]})")
    
    # Current (Dot Product)
    print("\n--- Dot Product Recs ---")
    recs_a = rec.recommend_from_history([asins_input[0]], k=5)
    recs_b = rec.recommend_from_history([asins_input[1]], k=5)
    
    set_a = set(r['asin'] for r in recs_a)
    set_b = set(r['asin'] for r in recs_b)
    overlap = set_a.intersection(set_b)
    print(f"Item A Recs: {set_a}")
    print(f"Item B Recs: {set_b}")
    print(f"Overlap: {len(overlap)} / 5")
    
    if len(overlap) >= 4:
        print(">> HIGH OVERLAP detected with Dot Product.")
        
    # Proposed (Cosine Similarity)
    print("\n--- Cosine Similarity Simulation ---")
    # Normalize inputs
    vec_a = factors[mid_indices[0]].reshape(1, -1)
    vec_b = factors[mid_indices[1]].reshape(1, -1)
    # Normalize all factors
    factors_norm = normalize(factors, axis=1)
    
    # Scores
    scores_a = factors_norm.dot(normalize(vec_a, axis=1).T).flatten()
    scores_b = factors_norm.dot(normalize(vec_b, axis=1).T).flatten()
    
    # Top K
    top_a = np.argsort(scores_a)[::-1][:5] # self is usually top 1, so take 5
    top_b = np.argsort(scores_b)[::-1][:5]
    
    asins_a_sim = set(encoder.inverse_transform(top_a))
    asins_b_sim = set(encoder.inverse_transform(top_b))
    
    print(f"Item A Cosine Recs: {asins_a_sim}")
    print(f"Item B Cosine Recs: {asins_b_sim}")
    overlap_sim = asins_a_sim.intersection(asins_b_sim)
    print(f"Cosine Overlap: {len(overlap_sim)} / 5")

if __name__ == "__main__":
    debug_bias()
