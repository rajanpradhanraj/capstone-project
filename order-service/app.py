# Order Service
# Manages cart and order processing

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import requests
import json

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "orders.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Product Catalog Service URL
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:5001')

db = SQLAlchemy(app)

# Models
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # For simplicity, using string user_id
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to order items
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.order_items]
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.price * self.quantity
        }

# Helper Functions
def get_product_details(product_id):
    """Fetch product details from Product Catalog Service"""
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}')
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None

def validate_stock_with_product_service(items):
    """Validate stock with Product Catalog Service"""
    try:
        response = requests.post(
            f'{PRODUCT_SERVICE_URL}/products/validate-stock',
            json={'items': items},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            return response.json()
        return {'valid': False, 'error': 'Stock validation failed'}
    except requests.RequestException as e:
        return {'valid': False, 'error': f'Service communication error: {str(e)}'}

def update_stock_in_product_service(items):
    """Update stock in Product Catalog Service"""
    try:
        response = requests.post(
            f'{PRODUCT_SERVICE_URL}/products/update-stock',
            json={'items': items},
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'order-service'})

# Cart Management
@app.route('/cart', methods=['GET'])
def get_cart():
    try:
        user_id = request.headers.get('X-User-ID', 'user1')
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        cart_data = []
        total_amount = 0
        
        for item in cart_items:
            # Get product details from Product Catalog Service
            product = get_product_details(item.product_id)
            if product:
                subtotal = product['price'] * item.quantity
                total_amount += subtotal
                
                cart_data.append({
                    'cart_id': item.id,
                    'product_id': item.product_id,
                    'product_name': product['name'],
                    'product_price': product['price'],
                    'product_image': product.get('image_url', ''),
                    'quantity': item.quantity,
                    'subtotal': subtotal,
                    'available_stock': product['stock']
                })
        
        return jsonify({
            'user_id': user_id,
            'items': cart_data,
            'total_amount': total_amount,
            'item_count': len(cart_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID', 'user1')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({'error': 'product_id is required'}), 400
        
        # Validate product exists
        product = get_product_details(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check if item already exists in cart
        existing_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.utcnow()
        else:
            # Add new item
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({'message': 'Item added to cart successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cart/update', methods=['PUT'])
def update_cart_item():
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID', 'user1')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        if not product_id or quantity is None:
            return jsonify({'error': 'product_id and quantity are required'}), 400
        
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Cart updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cart/remove', methods=['DELETE'])
def remove_from_cart():
    try:
        data = request.get_json()
        user_id = request.headers.get('X-User-ID', 'user1')
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'product_id is required'}), 400
        
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({'message': 'Item removed from cart successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    try:
        user_id = request.headers.get('X-User-ID', 'user1')
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'Cart cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Order Management
@app.route('/orders/checkout', methods=['POST'])
def checkout():
    try:
        user_id = request.headers.get('X-User-ID', 'user1')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Get cart items
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Prepare items for stock validation
        stock_items = [
            {'product_id': item.product_id, 'quantity': item.quantity}
            for item in cart_items
        ]
        
        # Validate stock with Product Catalog Service
        stock_validation = validate_stock_with_product_service(stock_items)
        if not stock_validation.get('valid'):
            return jsonify({
                'error': 'Stock validation failed',
                'details': stock_validation
            }), 400
        
        # Calculate total and create order
        total_amount = 0
        order_items_data = []
        
        for item in cart_items:
            product = get_product_details(item.product_id)
            if not product:
                return jsonify({'error': f'Product {item.product_id} not found'}), 404
            
            subtotal = product['price'] * item.quantity
            total_amount += subtotal
            
            order_items_data.append({
                'product_id': item.product_id,
                'product_name': product['name'],
                'price': product['price'],
                'quantity': item.quantity
            })
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                price=item_data['price'],
                quantity=item_data['quantity']
            )
            db.session.add(order_item)
        
        # Update stock in Product Catalog Service
        if update_stock_in_product_service(stock_items):
            # Stock updated successfully, confirm order
            order.status = 'confirmed'
            
            # Clear cart
            Cart.query.filter_by(user_id=user_id).delete()
            
            db.session.commit()
            
            return jsonify({
                'message': 'Order placed successfully',
                'order': order.to_dict()
            }), 201
        else:
            # Stock update failed, rollback
            db.session.rollback()
            return jsonify({'error': 'Failed to update stock. Order cancelled.'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/orders/history', methods=['GET'])
def get_order_history():
    try:
        user_id = request.headers.get('X-User-ID', 'user1')
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify(order.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        
        order = Order.query.get_or_404(order_id)
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(order.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin routes
@app.route('/admin/orders', methods=['GET'])
def get_all_orders():
    try:
        status = request.args.get('status')
        query = Order.query
        
        if status:
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/dashboard', methods=['GET'])
def get_dashboard_data():
    try:
        # Get total orders
        total_orders = Order.query.count()
        
        # Get total revenue
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        
        # Get order status counts
        order_status_counts = {}
        for status in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
            count = Order.query.filter_by(status=status).count()
            if count > 0:
                order_status_counts[status] = count
        
        # Get recent orders (last 5)
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        # Get product data from product service
        try:
            response = requests.get(f'{PRODUCT_SERVICE_URL}/products')
            if response.status_code == 200:
                products = response.json()
                total_products = len(products)
                low_stock_items = [p for p in products if p.get('stock', 0) < 5]
                low_stock_products = len(low_stock_items)
            else:
                total_products = 0
                low_stock_products = 0
                low_stock_items = []
        except requests.RequestException:
            total_products = 0
            low_stock_products = 0
            low_stock_items = []
        
        dashboard_data = {
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'low_stock_products': low_stock_products,
            'order_status_counts': order_status_counts,
            'recent_orders': [order.to_dict() for order in recent_orders],
            'low_stock_items': low_stock_items[:5]  # Only show first 5
        }
        
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True, host='0.0.0.0', port=5002)
