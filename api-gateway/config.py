import os

class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET", "devsecret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET", "devsecret")
    
    db_path = "data/gateway.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "GATEWAY_DATABASE_URL",
        f"sqlite:///{db_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://localhost:5001")
    ORDER_SERVICE_URL   = os.environ.get("ORDER_SERVICE_URL",   "http://localhost:5002")
    CORS_ORIGINS        = os.environ.get("CORS_ORIGINS", "http://localhost:4200")
