from app import app
from models import db, Product

with app.app_context():
    count = Product.query.count()
    print(f"Total products in SQL Database: {count}")
