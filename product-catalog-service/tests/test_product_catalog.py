import unittest
import json
import tempfile
import os
from datetime import datetime
from product_catalog import app, db, Product

class ProductCatalogTestCase(unittest.TestCase):
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
        
        # Create test products
        self.create_test_products()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def create_test_products(self):
        """Create sample test products"""
        products = [
            Product(
                name='Test Laptop',
                description='A test laptop for testing',
                price=999.99,
                stock=10,
                category='Electronics',
                image_url='http://example.com/laptop.jpg'
            ),
            Product(
                name='Test Phone',
                description='A test phone for testing',
                price=599.99,
                stock=15,
                category='Electronics',
                image_url='http://example.com/phone.jpg'
            ),
            Product(
                name='Test Book',
                description='A test book for testing',
                price=19.99,
                stock=50,
                category='Books',
                image_url='http://example.com/book.jpg'
            )
        ]
        
        for product in products:
            db.session.add(product)
        db.session.commit()

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'product-catalog')

    def test_get_all_products(self):
        """Test getting all products"""
        response = self.app.get('/products')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 3)
        
        # Check if all products have required fields
        for product in data:
            self.assertIn('id', product)
            self.assertIn('name', product)
            self.assertIn('price', product)
            self.assertIn('stock', product)

    def test_get_product_by_id(self):
        """Test getting a specific product by ID"""
        # Get first product
        response = self.app.get('/products/1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['name'], 'Test Laptop')
        self.assertEqual(data['price'], 999.99)
        self.assertEqual(data['category'], 'Electronics')

    def test_get_nonexistent_product(self):
        """Test getting a product that doesn't exist"""
        response = self.app.get('/products/999')
        
        self.assertEqual(response.status_code, 404)

    def test_create_product_success(self):
        """Test successful product creation"""
        product_data = {
            'name': 'New Test Product',
            'description': 'A new test product',
            'price': 29.99,
            'stock': 25,
            'category': 'Test Category',
            'image_url': 'http://example.com/new.jpg'
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['name'], 'New Test Product')
        self.assertEqual(data['price'], 29.99)
        
        # Verify product was created in database
        product = Product.query.filter_by(name='New Test Product').first()
        self.assertIsNotNone(product)
        self.assertEqual(product.stock, 25)

    def test_create_product_missing_required_fields(self):
        """Test product creation with missing required fields"""
        # Missing name
        product_data = {
            'description': 'A test product',
            'price': 29.99
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Missing price
        product_data = {
            'name': 'Test Product',
            'description': 'A test product'
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_create_product_invalid_price(self):
        """Test product creation with invalid price"""
        product_data = {
            'name': 'Test Product',
            'description': 'A test product',
            'price': 'invalid_price'
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_update_product_success(self):
        """Test successful product update"""
        update_data = {
            'name': 'Updated Laptop',
            'price': 1099.99,
            'stock': 5
        }
        
        response = self.app.put('/products/1',
                              data=json.dumps(update_data),
                              content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['name'], 'Updated Laptop')
        self.assertEqual(data['price'], 1099.99)
        self.assertEqual(data['stock'], 5)
        
        # Verify database was updated
        product = Product.query.get(1)
        self.assertEqual(product.name, 'Updated Laptop')
        self.assertEqual(product.price, 1099.99)

    def test_update_nonexistent_product(self):
        """Test updating a product that doesn't exist"""
        update_data = {'name': 'Updated Product'}
        
        response = self.app.put('/products/999',
                              data=json.dumps(update_data),
                              content_type='application/json')
        
        self.assertEqual(response.status_code, 404)

    def test_delete_product_success(self):
        """Test successful product deletion"""
        response = self.app.delete('/products/1')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify product was deleted from database
        product = Product.query.get(1)
        self.assertIsNone(product)

    def test_delete_nonexistent_product(self):
        """Test deleting a product that doesn't exist"""
        response = self.app.delete('/products/999')
        
        self.assertEqual(response.status_code, 404)

    def test_search_products_by_category(self):
        """Test searching products by category"""
        response = self.app.get('/products?category=Electronics')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        
        for product in data:
            self.assertIn('Electronics', product['category'])

    def test_search_products_by_name(self):
        """Test searching products by name"""
        response = self.app.get('/products?search=laptop')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertIn('Laptop', data[0]['name'])

    def test_search_products_by_description(self):
        """Test searching products by description"""
        response = self.app.get('/products?search=testing')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 3)  # All products have 'testing' in description

    def test_search_products_combined_filters(self):
        """Test searching with both category and search filters"""
        response = self.app.get('/products?category=Electronics&search=laptop')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Laptop')

    def test_product_model_to_dict(self):
        """Test Product model to_dict method"""
        product = Product.query.get(1)
        product_dict = product.to_dict()
        
        self.assertIn('id', product_dict)
        self.assertIn('name', product_dict)
        self.assertIn('price', product_dict)
        self.assertIn('stock', product_dict)
        self.assertIn('category', product_dict)
        self.assertIn('created_at', product_dict)
        self.assertIn('updated_at', product_dict)

    def test_product_creation_timestamps(self):
        """Test that timestamps are set correctly"""
        product_data = {
            'name': 'Timestamp Test Product',
            'price': 99.99
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
        
        # Verify timestamps are recent
        created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        self.assertLess((datetime.utcnow() - created_at).total_seconds(), 10)

    def test_stock_validation(self):
        """Test stock validation"""
        # Test negative stock
        product_data = {
            'name': 'Negative Stock Product',
            'price': 99.99,
            'stock': -5
        }
        
        response = self.app.post('/products',
                               data=json.dumps(product_data),
                               content_type='application/json')
        
        # Should still work (stock can be negative in this implementation)
        self.assertEqual(response.status_code, 201)

if __name__ == '__main__':
    unittest.main()
