from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Product, Interaction, CartItem, WishlistItem, Review
from recommender import Recommender
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key'
# MySQL Configuration (XAMPP default)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/beauty_reco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Recommender
recommender = Recommender()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context Processor to inject main categories or checks if needed
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.route('/')
def index():
    recommendations = []
    if current_user.is_authenticated:
        # Fetch recent interactions for Live Recommendations
        recent_interactions = Interaction.query.filter_by(user_id=current_user.id)\
            .order_by(Interaction.timestamp.desc())\
            .limit(20).all()
        recent_asins = [i.product_asin for i in recent_interactions]
        
        if recent_asins:
            print(f"DEBUG: User {current_user.username} has interactions: {recent_asins[:5]}...")
            recommendations = recommender.recommend(current_user.username, recent_asins=recent_asins, k=8)
            print(f"DEBUG: Generated {len(recommendations)} recommendations.")
        else:
            print("DEBUG: No recent interactions found for user.")
    
    # Cold start / Popular items for homepage (always shown as Trending)
    products = recommender.get_cold_start_items(12)
    return render_template('index.html', products=products, recommendations=recommendations, title="Home")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', title="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('recommend')) # Direct to recommendations after login
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/recommend')
def recommend():
    if current_user.is_authenticated:
        # Fetch recent interactions (Live Data)
        recent_interactions = Interaction.query.filter_by(user_id=current_user.id)\
            .order_by(Interaction.timestamp.desc())\
            .limit(20).all()
        
        recent_asins = [i.product_asin for i in recent_interactions]
        
        # Personalized recommendations
        products = recommender.recommend(current_user.username, recent_asins=recent_asins, k=12)
        return render_template('recommend.html', products=products, title="Your Recommendations")
        flash('Log in to see personalized recommendations!', 'info')
        return render_template('index.html', products=products, title="Popular Products")

@app.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    query = Product.query
    
    if search_query:
        query = query.filter(Product.title.ilike(f'%{search_query}%'))
        
    if category:
        query = query.filter(Product.main_cat == category)
        
    # Fetch unique categories for filter
    categories = [r[0] for r in db.session.query(Product.main_cat).distinct().order_by(Product.main_cat).all() if r[0]]
    
    # Fetch paginated products from DB
    products_pagination = query.order_by(Product.popularity.desc()).paginate(page=page, per_page=20)
    
    return render_template('products.html', products=products_pagination, title="Shop All",
                           categories=categories, current_category=category, search_query=search_query)

@app.route('/product/<asin>')
def product_detail(asin):
    # Ensure product exists in DB (Lazy Loading) to satisfy Foreign Key
    product_db = Product.query.get(asin)
    if not product_db:
        # Fetch from recommender metadata
        product_data = recommender.get_product_details([asin])
        if product_data:
            p_info = product_data[0]
            # Create new Product entry
            product_db = Product(
                asin=p_info.get('asin', asin),
                title=p_info.get('title'),
                brand=p_info.get('brand'),
                main_cat=p_info.get('main_cat'),
                image_url=p_info.get('image_url')
            )
            try:
                db.session.add(product_db)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error adding product to DB: {e}")

    # Log interaction
    # Log interaction
    if current_user.is_authenticated and product_db:
        interaction = Interaction(user_id=current_user.id, product_asin=asin, interaction_type='view')
        db.session.add(interaction)
        db.session.commit()
    
    # Get product details (using recommender helper)
    products = recommender.get_product_details([asin])
    product = products[0] if products else None
    
    if not product:
        flash('Product not found', 'warning')
        return redirect(url_for('index'))
    
    # Get reviews from SQL DB
    reviews = Review.query.filter_by(product_asin=asin).order_by(Review.timestamp.desc()).all()
        
    return render_template('product.html', product=product, reviews=reviews, title=product.get('title', 'Product'))

@app.route('/add_review/<asin>', methods=['POST'])
@login_required
def add_review(asin):
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if not rating:
        flash('Please select a rating.', 'warning')
        return redirect(url_for('product_detail', asin=asin))
        
    rating = int(rating)
    
    # Save Review
    review = Review(
        user_id=current_user.id,
        product_asin=asin,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    
    # If high rating, count as implicit Positive Interaction
    if rating >= 4:
        # Create interaction
        interaction = Interaction(
             user_id=current_user.id,
             product_asin=asin,
             interaction_type='like'
        )
        db.session.add(interaction)
        
    db.session.commit()
    flash('Thank you for your review!', 'success')
    return redirect(url_for('product_detail', asin=asin))

@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    # Calculate total would go here
    return render_template('cart.html', items=items, title="Your Cart")

@app.route('/add_to_cart/<asin>')
@login_required
def add_to_cart(asin):
    # Check if item exists in cart
    item = CartItem.query.filter_by(user_id=current_user.id, product_asin=asin).first()
    if item:
        item.quantity += 1
    else:
        # Ensure product exists
        prod = Product.query.get(asin)
        if not prod:
            # Try to fetch meta to add it
            p_data = recommender.get_product_details([asin])
            if p_data:
                p_info = p_data[0]
                prod = Product(asin=asin, title=p_info.get('title'), image_url=p_info.get('image_url'))
                db.session.add(prod)
                db.session.commit()
        
        if prod:
            item = CartItem(user_id=current_user.id, product_asin=asin)
            db.session.add(item)
    
    db.session.commit()
    flash('Item added to cart', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/remove_from_cart/<int:id>')
@login_required
def remove_from_cart(id):
    item = CartItem.query.get_or_404(id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from cart', 'info')
    return redirect(url_for('cart'))

@app.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', items=items, title="Your Wishlist")

@app.route('/add_to_wishlist/<asin>')
@login_required
def add_to_wishlist(asin):
    exists = WishlistItem.query.filter_by(user_id=current_user.id, product_asin=asin).first()
    if not exists:
        # Ensure product exists
        prod = Product.query.get(asin)
        if not prod:
             p_data = recommender.get_product_details([asin])
             if p_data:
                 p_info = p_data[0]
                 prod = Product(asin=asin, title=p_info.get('title'), image_url=p_info.get('image_url'))
                 db.session.add(prod)
                 db.session.commit()
        
        if prod:
            item = WishlistItem(user_id=current_user.id, product_asin=asin)
            db.session.add(item)
            db.session.commit()
            flash('Added to wishlist', 'success')
    else:
        flash('Already in wishlist', 'info')
        
    return redirect(request.referrer or url_for('products'))

@app.route('/remove_from_wishlist/<int:id>')
@login_required
def remove_from_wishlist(id):
    item = WishlistItem.query.get_or_404(id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from wishlist', 'info')
    return redirect(url_for('wishlist'))

# Setup Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
