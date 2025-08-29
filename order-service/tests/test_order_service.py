import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, Mock
from order_service import app, db, Cart, Order, OrderItem

class OrderServiceTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test database and client"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test data
        self.create_test_data()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def create_test_data(self):
        """Create sample test data"""
        # Create test cart items
        cart_items = [
            Cart(user_id='user1', product_id=1, quantity=2),
            Cart(user_id='user1', product_id=2, quantity=1),
            Cart(user_id='user2', product_id=1, quantity=3)
        ]
        
        for item in cart_items:
            db.session.add(item)
        
        # Create test orders
        order1 = Order(user_id='user1', total_amount=1599.98, status='pending')
        order2 = Order(user_id='user2', total_amount=2999.97, status='confirmed')
        
        db.session.add(order1)
        db.session.add(order2)
        db.session.commit()
        
        # Create test order items
        order_items = [
            OrderItem(order_id=1, product_id=1, product_name='Test Laptop', price=999.99, quantity=1),
            OrderItem(order_id=1, product_id=2, product_name='Test Phone', price=599.99, quantity=1),
            OrderItem(order_id=2, product_id=1, product_name='Test Laptop', price=999.99, quantity=3)
        ]
        
        for item in order_items:
            db.session.add(item)
        
        db.session.commit()

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'order-service')

    # Cart Tests
    def test_get_cart(self):
        """Test getting user's cart"""
        response = self.app.get('/cart/user1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)  # user1 has 2 items in cart
        
        # Check cart item structure
        for item in data:
            self.assertIn('id', item)
            self.assertIn('product_id', item)
            self.assertIn('quantity', item)
            self.assertIn('user_id', item)

    def test_get_empty_cart(self):
        """Test getting cart for user with no items"""
        response = self.app.get('/cart/user3')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

    def test_add_to_cart_success(self):
        """Test successfully adding item to cart"""
        cart_data = {
            'user_id': 'user3',
            'product_id': 3,
            'quantity': 2
        }
        
        response = self.app.post('/cart/add',
                               data=json.dumps(cart_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['user_id'], 'user3')
        self.assertEqual(data['product_id'], 3)
        self.assertEqual(data['quantity'], 2)
        
        # Verify item was added to database
        cart_item = Cart.query.filter_by(user_id='user3', product_id=3).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 2)

    def test_add_to_cart_missing_fields(self):
        """Test adding to cart with missing fields"""
        # Missing user_id
        cart_data = {'product_id': 3, 'quantity': 2}
        response = self.app.post('/cart/add',
                               data=json.dumps(cart_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Missing product_id
        cart_data = {'user_id': 'user3', 'quantity': 2}
        response = self.app.post('/cart/add',
                               data=json.dumps(cart_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_update_cart_item(self):
        """Test updating cart item quantity"""
        update_data = {'quantity': 5}
        
        response = self.app.put('/cart/1',
                              data=json.dumps(update_data),
                              content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['quantity'], 5)
        
        # Verify database was updated
        cart_item = Cart.query.get(1)
        self.assertEqual(cart_item.quantity, 5)

    def test_remove_from_cart(self):
        """Test removing item from cart"""
        response = self.app.delete('/cart/1')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify item was removed from database
        cart_item = Cart.query.get(1)
        self.assertIsNone(cart_item)

    def test_clear_cart(self):
        """Test clearing entire user cart"""
        response = self.app.delete('/cart/clear/user1')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all items for user1 were removed
        cart_items = Cart.query.filter_by(user_id='user1').all()
        self.assertEqual(len(cart_items), 0)

    # Order Tests
    def test_get_user_orders(self):
        """Test getting user's orders"""
        response = self.app.get('/orders/user1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)  # user1 has 1 order
        
        # Check order structure
        order = data[0]
        self.assertIn('id', order)
        self.assertIn('total_amount', order)
        self.assertIn('status', order)
        self.assertIn('items', order)

    def test_get_order_by_id(self):
        """Test getting specific order by ID"""
        response = self.app.get('/orders/1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user_id'], 'user1')
        self.assertEqual(data['total_amount'], 1599.98)
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(len(data['items']), 2)

    def test_get_nonexistent_order(self):
        """Test getting order that doesn't exist"""
        response = self.app.get('/orders/999')
        
        self.assertEqual(response.status_code, 404)

    @patch('order_service.requests.get')
    def test_create_order_success(self, mock_get):
        """Test successful order creation"""
        # Mock product service response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 1,
            'name': 'Test Laptop',
            'price': 999.99,
            'stock': 10
        }
        
        order_data = {
            'user_id': 'user3',
            'items': [
                {'product_id': 1, 'quantity': 2}
            ]
        }
        
        response = self.app.post('/orders',
                               data=json.dumps(order_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['user_id'], 'user3')
        self.assertEqual(data['status'], 'pending')
        self.assertIn('id', data)
        
        # Verify order was created in database
        order = Order.query.filter_by(user_id='user3').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, 1999.98)  # 999.99 * 2

    def test_create_order_missing_fields(self):
        """Test order creation with missing fields"""
        # Missing user_id
        order_data = {'items': [{'product_id': 1, 'quantity': 2}]}
        response = self.app.post('/orders',
                               data=json.dumps(order_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Missing items
        order_data = {'user_id': 'user3'}
        response = self.app.post('/orders',
                               data=json.dumps(order_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_create_order_empty_items(self):
        """Test order creation with empty items list"""
        order_data = {
            'user_id': 'user3',
            'items': []
        }
        
        response = self.app.post('/orders',
                               data=json.dumps(order_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_update_order_status(self):
        """Test updating order status"""
        update_data = {'status': 'shipped'}
        
        response = self.app.put('/orders/1/status',
                              data=json.dumps(update_data),
                              content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'shipped')
        
        # Verify database was updated
        order = Order.query.get(1)
        self.assertEqual(order.status, 'shipped')

    def test_update_order_invalid_status(self):
        """Test updating order with invalid status"""
        update_data = {'status': 'invalid_status'}
        
        response = self.app.put('/orders/1/status',
                              data=json.dumps(update_data),
                              content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_cancel_order(self):
        """Test canceling an order"""
        response = self.app.put('/orders/1/cancel')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'cancelled')
        
        # Verify database was updated
        order = Order.query.get(1)
        self.assertEqual(order.status, 'cancelled')

    # Model Tests
    def test_cart_model_to_dict(self):
        """Test Cart model to_dict method"""
        cart_item = Cart.query.get(1)
        cart_dict = cart_item.to_dict()
        
        self.assertIn('id', cart_dict)
        self.assertIn('user_id', cart_dict)
        self.assertIn('product_id', cart_dict)
        self.assertIn('quantity', cart_dict)
        self.assertIn('created_at', cart_dict)
        self.assertIn('updated_at', cart_dict)

    def test_order_model_to_dict(self):
        """Test Order model to_dict method"""
        order = Order.query.get(1)
        order_dict = order.to_dict()
        
        self.assertIn('id', order_dict)
        self.assertIn('user_id', order_dict)
        self.assertIn('total_amount', order_dict)
        self.assertIn('status', order_dict)
        self.assertIn('items', order_dict)
        self.assertIn('created_at', order_dict)
        self.assertIn('updated_at', order_dict)

    def test_order_item_model_to_dict(self):
        """Test OrderItem model to_dict method"""
        order_item = OrderItem.query.get(1)
        item_dict = order_item.to_dict()
        
        self.assertIn('id', item_dict)
        self.assertIn('order_id', item_dict)
        self.assertIn('product_id', item_dict)
        self.assertIn('product_name', item_dict)
        self.assertIn('price', item_dict)
        self.assertIn('quantity', item_dict)
        self.assertIn('subtotal', item_dict)
        
        # Test subtotal calculation
        expected_subtotal = order_item.price * order_item.quantity
        self.assertEqual(item_dict['subtotal'], expected_subtotal)

    def test_order_relationships(self):
        """Test order relationships"""
        order = Order.query.get(1)
        
        # Test order items relationship
        self.assertEqual(len(order.order_items), 2)
        
        # Test order item backref
        order_item = order.order_items[0]
        self.assertEqual(order_item.order, order)

    def test_cart_timestamps(self):
        """Test that cart timestamps are set correctly"""
        cart_data = {
            'user_id': 'user4',
            'product_id': 4,
            'quantity': 1
        }
        
        response = self.app.post('/cart/add',
                               data=json.dumps(cart_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
        
        # Verify timestamps are recent
        created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        self.assertLess((datetime.utcnow() - created_at).total_seconds(), 10)

    def test_order_timestamps(self):
        """Test that order timestamps are set correctly"""
        order = Order.query.get(1)
        
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)
        
        # Test that updated_at changes when status changes
        original_updated = order.updated_at
        order.status = 'delivered'
        db.session.commit()
        
        self.assertGreater(order.updated_at, original_updated)

if __name__ == '__main__':
    unittest.main()
