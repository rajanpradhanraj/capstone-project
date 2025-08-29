import unittest
import json
import tempfile
import os
from api_gateway import app, db, User
from werkzeug.security import generate_password_hash

class APIGatewayTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test database and client"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username='testuser',
            password=generate_password_hash('testpass123'),
            role='user'
        )
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_home_endpoint(self):
        """Test the home endpoint"""
        response = self.app.get('/')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', data)
        self.assertIn('API Gateway', data['message'])

    def test_register_success(self):
        """Test successful user registration"""
        user_data = {
            'username': 'newuser',
            'password': 'newpass123',
            'role': 'user'
        }
        
        response = self.app.post('/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['message'], 'User created successfully')
        
        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'user')

    def test_register_missing_fields(self):
        """Test registration with missing fields"""
        # Missing password
        user_data = {'username': 'testuser'}
        response = self.app.post('/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Missing username
        user_data = {'password': 'testpass'}
        response = self.app.post('/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_username(self):
        """Test registration with existing username"""
        user_data = {
            'username': 'testuser',  # Already exists
            'password': 'newpass123'
        }
        
        response = self.app.post('/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', json.loads(response.data)['message'])

    def test_login_success(self):
        """Test successful login"""
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.app.post('/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Login successful')
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['role'], 'user')

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Wrong password
        login_data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = self.app.post('/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        
        # Non-existent user
        login_data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        
        response = self.app.post('/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        # Missing password
        login_data = {'username': 'testuser'}
        response = self.app.post('/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        # Missing username
        login_data = {'password': 'testpass123'}
        response = self.app.post('/login',
                               data=json.dumps(login_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_admin_user_creation(self):
        """Test creating admin user"""
        user_data = {
            'username': 'adminuser',
            'password': 'adminpass123',
            'role': 'admin'
        }
        
        response = self.app.post('/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        # Verify admin role was set
        user = User.query.filter_by(username='adminuser').first()
        self.assertEqual(user.role, 'admin')

    def test_user_model_repr(self):
        """Test User model string representation"""
        user = User.query.filter_by(username='testuser').first()
        self.assertEqual(str(user), '<User testuser>')

    def test_password_hashing(self):
        """Test password hashing and verification"""
        user = User.query.filter_by(username='testuser').first()
        
        # Password should be hashed
        self.assertNotEqual(user.password, 'testpass123')
        
        # Should verify correctly
        from werkzeug.security import check_password_hash
        self.assertTrue(check_password_hash(user.password, 'testpass123'))

if __name__ == '__main__':
    unittest.main()
