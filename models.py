from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Relationship to interactions
    interactions = db.relationship('Interaction', backref='user', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    asin = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.Text, nullable=True)
    brand = db.Column(db.String(200), nullable=True)
    main_cat = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    popularity = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)

class Interaction(db.Model):
    __tablename__ = 'interactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_asin = db.Column(db.String(50), db.ForeignKey('products.asin'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    interaction_type = db.Column(db.String(20), default='view')

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_asin = db.Column(db.String(50), db.ForeignKey('products.asin'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Relationships
    product = db.relationship('Product', backref='cart_inclusions')
    user = db.relationship('User', backref='cart_items')

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_asin = db.Column(db.String(50), db.ForeignKey('products.asin'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='wishlist_inclusions')
    user = db.relationship('User', backref='wishlist_items')

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_asin = db.Column(db.String(50), db.ForeignKey('products.asin'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='reviews')
    user = db.relationship('User', backref='reviews')
