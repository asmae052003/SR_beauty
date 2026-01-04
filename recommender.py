import os
import joblib
import pandas as pd
import numpy as np
import scipy.sparse
import pickle

# Configuration
ARTIFACTS_DIR = 'artifacts'

class Recommender:
    def __init__(self):
        print("Loading artifacts...")
        # Load artifacts
        self.als_model = self.load_pickle("als_weighted.pkl")
        self.user_encoder = self.load_pickle("user_encoder.pkl")
        self.item_encoder = self.load_pickle("item_encoder.pkl")
        self.recent_items = self.load_pickle("recent_items.pkl")
        self.config = self.load_pickle("config.pkl")
        self.train_matrix = scipy.sparse.load_npz(os.path.join(ARTIFACTS_DIR, "train_matrix.npz"))
        
        # Load metadata
        self.meta_df = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
        # Ensure 'asin' is index for fast lookup
        if 'asin' in self.meta_df.columns:
            self.meta_df.set_index('asin', inplace=True)
            
        # Build category map for Content-Based Fallback
        self.category_map = {}
        if 'main_cat' in self.meta_df.columns:
            # Group by category
            grouped = self.meta_df.groupby('main_cat')
            for cat, group in grouped:
                self.category_map[cat] = group.index.tolist()
        
        print("Artifacts loaded successfully.")

    def load_pickle(self, filename):
        path = os.path.join(ARTIFACTS_DIR, filename)
        with open(path, "rb") as f:
            return pickle.load(f)

    def get_product_details(self, asins):
        """Retrieve product details from SQL Database (source of truth)."""
        # Lazy import to avoid circular dependency
        from models import Product
        
        # Query DB for these ASINs
        # We need to preserve order, so we fetch all then reorder
        products_db = Product.query.filter(Product.asin.in_(asins)).all()
        
        # Create a map for fast lookup
        product_map = {p.asin: p for p in products_db}
        
        final_products = []
        for asin in asins:
            p = product_map.get(asin)
            if p:
                # Convert to dict
                p_dict = {
                    'asin': p.asin,
                    'title': p.title,
                    'brand': p.brand,
                    'main_cat': p.main_cat,
                    'image_url': p.image_url,
                    'price': None, # SQL model doesn't have price yet
                    'avg_rating': p.avg_rating,
                    'popularity': p.popularity
                }
                final_products.append(p_dict)
                
        # Clean up image_urls (legacy check if DB has weird formats)
        for p in final_products:
            img = p.get('image_url')
            if isinstance(img, str) and img.startswith("['") and img.endswith("']"):
                try:
                    import ast
                    actual_list = ast.literal_eval(img)
                    if actual_list:
                        p['image_url'] = actual_list[0]
                except:
                    pass
            # If no image, placeholder
            if not p.get('image_url'):
                p['image_url'] = "https://via.placeholder.com/300x300?text=No+Image"
                
        return final_products

    def recommend(self, username, recent_asins=None, k=10):
        """
        Main recommendation function.
        Returns a list of product dictionaries.
        """
        if recent_asins is None:
            recent_asins = []

        # 1. Translate username to user_idx
        user_idx = None
        if username in self.user_encoder.classes_:
            user_idx = self.user_encoder.transform([username])[0]

        # 2. Check if user needs "Live" recommendations (New User or Low History but has Session Data)
        # If user is unknown OR has little history in training data, try to use recent_asins
        use_live_recs = False
        if user_idx is None:
            use_live_recs = True
        else:
            # Check training history
            user_interaction_count = self.train_matrix[user_idx].nnz
            threshold = self.config.get('cold_threshold', 3)
            if user_interaction_count < threshold:
                use_live_recs = True

        # If we should use live recs and have data
        if use_live_recs and recent_asins:
            print(f"User {username} is cold-start but has {len(recent_asins)} recent interactions. Using Hybrid/Content logic.")
            return self.recommend_from_history(recent_asins, k=k)
            
        # Fallback to pure Cold Start if no user_idx and no history
        if user_idx is None:
            print(f"User {username} not in encoder and no history. Cold start.")
            return self.get_cold_start_items(k)

        # 3. Standard Matrix Factorization Score (for existing users)
        try:
            user_factors = self.als_model.user_factors[user_idx]
            item_factors = self.als_model.item_factors
            
            scores = item_factors.dot(user_factors)

            # Filter already liked items from training data
            liked_indices = self.train_matrix[user_idx].indices
            scores[liked_indices] = -np.inf

            # Also filter items currently in recent_asins (don't recommend what they just saw)
            # Convert recent_asins to indices
            for asin in recent_asins:
                if asin in self.item_encoder.classes_:
                    idx = self.item_encoder.transform([asin])[0]
                    scores[idx] = -np.inf

            top_indices = np.argsort(scores)[::-1][:k]
            top_asins = self.item_encoder.inverse_transform(top_indices.astype(int))
            return self.get_product_details(top_asins)

        except Exception as e:
            print(f"Error during recommendation: {e}")
            import traceback
            traceback.print_exc()
            return self.get_cold_start_items(k)

    def recommend_by_category(self, asins, k=10):
        """
        Fallback: Recommend items from the same category as the input asins.
        """
        cats = []
        for asin in asins:
            if asin in self.meta_df.index:
                c = self.meta_df.loc[asin, 'main_cat']
                if c: cats.append(c)
        
        if not cats:
            return self.get_cold_start_items(k)
            
        # Pick most frequent category
        from collections import Counter
        target_cat = Counter(cats).most_common(1)[0][0]
        
        print(f"ALS Fallback: Recommending items from category '{target_cat}'")
        
        candidates = self.category_map.get(target_cat, [])
        # Remove inputs
        candidates = [c for c in candidates if c not in asins]
        
        if not candidates:
            return self.get_cold_start_items(k)
            
        # Sample random k
        import random
        # Seed for stability? No, we want diversity!
        start_k = min(len(candidates), k)
        sampled_asins = random.sample(candidates, start_k)
        
        return self.get_product_details(sampled_asins)

    def recommend_from_history(self, asins, k=10):
        """
        Generate recommendations by averaging the vectors of viewed items.
        simulating a "user vector" from their recent history.
        """
        valid_indices = []
        for asin in asins:
            if asin in self.item_encoder.classes_:
                idx = self.item_encoder.transform([asin])[0]
                valid_indices.append(idx)
        
        if not valid_indices:
            print("No valid ALS indices for inputs. Switching to Content-Based Fallback.")
            return self.recommend_by_category(asins, k=k)

        # Get factors for these items
        # shape: (num_viewed, n_factors)
        viewed_factors = self.als_model.item_factors[valid_indices]
        
        # Average them to get a temporary user profile
        # shape: (n_factors,)
        user_profile = np.mean(viewed_factors, axis=0)
        
        # USE COSINE SIMILARITY to avoid Popularity Bias (Magnitude Bias)
        # Normalize user profile
        from sklearn.preprocessing import normalize
        user_profile_norm = normalize(user_profile.reshape(1, -1), axis=1).flatten()
        
        # Normalize item factors (all)
        item_factors_norm = normalize(self.als_model.item_factors, axis=1)
        
        # Calculate scores (Cosine Similarity)
        scores = item_factors_norm.dot(user_profile_norm)
        
        # Filter out the items they already viewed
        scores[valid_indices] = -np.inf
        
        # Top K
        top_indices = np.argsort(scores)[::-1][:k]
        top_asins = self.item_encoder.inverse_transform(top_indices.astype(int))
        
        return self.get_product_details(top_asins)

    def get_cold_start_items(self, k=10):
        """Return popular/recent items."""
        # recent_items are integer indices, need to be converted to ASINs (strings)
        if isinstance(self.recent_items, list):
             # Take MORE than k, because some might not be in metadata
             # We take up to 300 to be safe
             limit = min(len(self.recent_items), 300)
             item_indices = self.recent_items[:limit]
             
             # Check if they are integers (model indices) or strings
             if item_indices and isinstance(item_indices[0], (int, np.integer)):
                 asins = self.item_encoder.inverse_transform(item_indices)
             else:
                 asins = item_indices
                 
             # Filter valid ones by checking metadata existence
             valid_asins = [a for a in asins if a in self.meta_df.index]
             # Return top k
             final_asins = valid_asins[:k]
        else:
            final_asins = []
            
        return self.get_product_details(final_asins)
