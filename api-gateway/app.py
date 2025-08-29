import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------
# Initialize Flask app
# ----------------------------
app = Flask(__name__)

# ----------------------------
# Database Config (SQLite)
# ----------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite3")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ----------------------------
# JWT Config (future use)
# ----------------------------
app.config["SECRET_KEY"] = "supersecretkey"  # change this for production
app.config["JWT_EXPIRATION_DELTA"] = timedelta(hours=1)

# ----------------------------
# Init DB + Migrate + CORS
# ----------------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# ----------------------------
# User Model
# ----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user or admin

    def __repr__(self):
        return f"<User {self.username}>"

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def home():
    return {"message": "API Gateway running with SQLite + JWT"}

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")  # default to "user"

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "username": user.username,
        "role": user.role
    }), 200

# ----------------------------
# Proxy routes for microservices
# ----------------------------
import requests

# Product service proxy
@app.route("/api/products", methods=["GET", "POST"])
@app.route("/api/products/<int:product_id>", methods=["GET", "PUT", "DELETE"])
def proxy_products(product_id=None):
    product_service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:5001')
    
    if product_id:
        url = f"{product_service_url}/products/{product_id}"
    else:
        url = f"{product_service_url}/products"
    
    # Forward query parameters
    params = request.args.to_dict()
    
    try:
        if request.method == "GET":
            response = requests.get(url, params=params)
        elif request.method == "POST":
            response = requests.post(url, json=request.get_json(), params=params)
        elif request.method == "PUT":
            response = requests.put(url, json=request.get_json(), params=params)
        elif request.method == "DELETE":
            response = requests.delete(url, params=params)
            
        return jsonify(response.json()) if response.content else "", response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Product service unavailable: {str(e)}"}), 503

# Authentication routes with /api prefix
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }), 200

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")  # default to "user"

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role
        }
    }), 201

@app.route("/api/auth/users", methods=["GET"])
def api_get_users():
    users = User.query.all()
    return jsonify({
        "users": [{"id": user.id, "username": user.username, "role": user.role} for user in users]
    }), 200

# Cart and Order service proxy
@app.route("/api/cart", methods=["GET"])
@app.route("/api/cart/<action>", methods=["POST", "PUT", "DELETE"])
def proxy_cart(action=None):
    order_service_url = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5002')
    user_id = request.headers.get('X-User-ID', 'user1')
    
    if action:
        url = f"{order_service_url}/cart/{action}"
    else:
        url = f"{order_service_url}/cart"
    
    try:
        headers = {'X-User-ID': user_id}
        
        if request.method == "GET":
            response = requests.get(url, headers=headers)
        elif request.method == "POST":
            response = requests.post(url, json=request.get_json(), headers=headers)
        elif request.method == "PUT":
            response = requests.put(url, json=request.get_json(), headers=headers)
        elif request.method == "DELETE":
            response = requests.delete(url, json=request.get_json(), headers=headers)
            
        return jsonify(response.json()) if response.content else "", response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Order service unavailable: {str(e)}"}), 503

# Orders proxy
@app.route("/api/orders/<action>", methods=["GET", "POST"])
@app.route("/api/orders/<int:order_id>", methods=["GET"])
def proxy_orders(action=None, order_id=None):
    order_service_url = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5002')
    user_id = request.headers.get('X-User-ID', 'user1')
    
    if order_id:
        url = f"{order_service_url}/orders/{order_id}"
    else:
        url = f"{order_service_url}/orders/{action}"
    
    try:
        headers = {'X-User-ID': user_id}
        
        if request.method == "GET":
            response = requests.get(url, headers=headers)
        elif request.method == "POST":
            response = requests.post(url, json=request.get_json(), headers=headers)
            
        return jsonify(response.json()) if response.content else "", response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Order service unavailable: {str(e)}"}), 503

# Admin routes proxy
@app.route("/api/admin/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_admin(path):
    user_role = request.headers.get('X-User-Role', 'user')
    
    # Simple role check
    if user_role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    # Determine which service to proxy to
    if path.startswith('orders'):
        service_url = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5002')
        url = f"{service_url}/admin/{path}"
    elif path.startswith('products'):
        service_url = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:5001')
        url = f"{service_url}/admin/{path}"
    else:
        # Dashboard or other admin routes - could go to either service
        service_url = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5002')
        url = f"{service_url}/admin/{path}"
    
    try:
        user_id = request.headers.get('X-User-ID', 'admin')
        headers = {'X-User-ID': user_id, 'X-User-Role': user_role}
        
        if request.method == "GET":
            response = requests.get(url, headers=headers)
        elif request.method == "POST":
            response = requests.post(url, json=request.get_json(), headers=headers)
        elif request.method == "PUT":
            response = requests.put(url, json=request.get_json(), headers=headers)
        elif request.method == "DELETE":
            response = requests.delete(url, headers=headers)
            
        return jsonify(response.json()) if response.content else "", response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "api-gateway"})

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "healthy", "service": "api-gateway"})

# ----------------------------
# Initialize database
# ----------------------------
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create default users if they don't exist
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('password'),
                role='admin'
            )
            db.session.add(admin_user)
        
        if not User.query.filter_by(username='user1').first():
            user1 = User(
                username='user1',
                password=generate_password_hash('password'),
                role='user'
            )
            db.session.add(user1)
        
        db.session.commit()

# ----------------------------
# Run the app
# ----------------------------
if __name__ == "__main__":
    create_tables()  # Initialize database
    app.run(debug=True, host="0.0.0.0", port=5000)

