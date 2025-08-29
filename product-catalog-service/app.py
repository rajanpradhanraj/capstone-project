# Product Catalog Service
# Manages products and inventory

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "products.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'product-catalog'})

@app.route('/products', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category')
        search = request.args.get('search')
        
        query = Product.query
        
        if category:
            query = query.filter(Product.category.ilike(f'%{category}%'))
        
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%')
                )
            )
        
        products = query.all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            stock=int(data.get('stock', 0)),
            category=data.get('category', ''),
            image_url=data.get('image_url', '')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'category' in data:
            product.category = data['category']
        if 'image_url' in data:
            product.image_url = data['image_url']
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(product.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/validate-stock', methods=['POST'])
def validate_stock():
    """Validate if requested quantities are available"""
    try:
        data = request.get_json()
        items = data.get('items', [])  # [{'product_id': 1, 'quantity': 2}, ...]
        
        validation_results = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            product = Product.query.get(product_id)
            if not product:
                validation_results.append({
                    'product_id': product_id,
                    'valid': False,
                    'reason': 'Product not found'
                })
                continue
            
            if product.stock >= quantity:
                validation_results.append({
                    'product_id': product_id,
                    'valid': True,
                    'available_stock': product.stock
                })
            else:
                validation_results.append({
                    'product_id': product_id,
                    'valid': False,
                    'reason': f'Insufficient stock. Available: {product.stock}, Requested: {quantity}',
                    'available_stock': product.stock
                })
        
        all_valid = all(result['valid'] for result in validation_results)
        
        return jsonify({
            'valid': all_valid,
            'items': validation_results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/update-stock', methods=['POST'])
def update_stock():
    """Update stock levels after order placement"""
    try:
        data = request.get_json()
        items = data.get('items', [])  # [{'product_id': 1, 'quantity': 2}, ...]
        
        # Start transaction
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            if product.stock < quantity:
                db.session.rollback()
                return jsonify({
                    'error': f'Insufficient stock for product {product_id}. Available: {product.stock}, Requested: {quantity}'
                }), 400
            
            product.stock -= quantity
            product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Stock updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Initialize database
def create_tables():
    db.create_all()
    
    # Add sample data if no products exist
    if Product.query.count() == 0:
        sample_products = [
            Product(
                name="Laptop Pro 15",
                description="High-performance laptop with 16GB RAM and 512GB SSD",
                price=89999.99,
                stock=25,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop"
            ),
            Product(
                name="Wireless Headphones",
                description="Premium noise-canceling wireless headphones",
                price=15999.99,
                stock=50,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop"
            ),
            Product(
                name="Coffee Maker",
                description="Programmable coffee maker with thermal carafe",
                price=7999.99,
                stock=15,
                category="Home & Kitchen",
                image_url="https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=400&h=300&fit=crop"
            ),
            Product(
                name="Running Shoes",
                description="Lightweight running shoes with excellent support",
                price=10999.99,
                stock=30,
                category="Sports",
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop"
            ),
            Product(
                name="Desk Chair",
                description="Ergonomic office chair with lumbar support",
                price=18999.99,
                stock=20,
                category="Furniture",
                image_url="https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop"
            ),
            Product(
                name="Smartphone X",
                description="Latest smartphone with 128GB storage and 48MP camera",
                price=64999.99,
                stock=40,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop"
            ),
            Product(
                name="Bluetooth Speaker",
                description="Portable waterproof speaker with 20-hour battery life",
                price=5999.99,
                stock=35,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop"
            ),
            Product(
                name="Kitchen Mixer",
                description="Professional stand mixer for baking enthusiasts",
                price=22999.99,
                stock=12,
                category="Home & Kitchen",
                image_url="https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop"
            ),
            Product(
                name="Yoga Mat",
                description="Non-slip yoga mat with carrying strap",
                price=3999.99,
                stock=60,
                category="Sports",
                image_url="https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=300&fit=crop"
            ),
            Product(
                name="Table Lamp",
                description="Modern LED table lamp with adjustable brightness",
                price=7999.99,
                stock=25,
                category="Home & Kitchen",
                image_url="https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=300&fit=crop"
            )
        ]
        
        for product in sample_products:
            db.session.add(product)
        
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True, host='0.0.0.0', port=5001)
