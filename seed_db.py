from app import app
from models import db, Product
from recommender import Recommender

def seed_products():
    print("Initializing Recommender to load metadata...")
    rec = Recommender()
    
    # rec.meta_df is a DataFrame with index 'asin'
    
    print(f"Found {len(rec.meta_df)} items in metadata.")
    
    # Convert to dict for easier iteration: {asin: {col: val, ...}}
    metadata_dict = rec.meta_df.to_dict(orient='index')
    
    inserted_count = 0
    updated_count = 0
    
    with app.app_context():
        # Get existing ASINs to avoid PK errors or redundant updates
        existing_asins = set(p.asin for p in Product.query.with_entities(Product.asin).all())
        print(f"Database currently has {len(existing_asins)} products.")
        
        batch = []
        BATCH_SIZE = 100
        
        for asin, data in metadata_dict.items():
            if asin in existing_asins:
                continue
                
            # Create new product
            new_prod = Product(
                asin=asin,
                title=data.get('title'),
                brand=data.get('brand'),
                main_cat=data.get('main_cat'),
                image_url=data.get('image_url')
                # popularity and avg_rating defaults to 0
            )
            batch.append(new_prod)
            
            if len(batch) >= BATCH_SIZE:
                db.session.add_all(batch)
                db.session.commit()
                inserted_count += len(batch)
                batch = []
                print(f"Inserted {inserted_count}...", end='\r')
        
        # Insert remaining
        if batch:
            db.session.add_all(batch)
            db.session.commit()
            inserted_count += len(batch)
            
        print(f"\nDone! Inserted {inserted_count} new products.")
        print(f"Total products in DB: {Product.query.count()}")

if __name__ == '__main__':
    seed_products()
