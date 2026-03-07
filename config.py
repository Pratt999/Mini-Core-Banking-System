import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    
    # PostgreSQL connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', 5432)}/" \
        f"{os.environ.get('DB_NAME', 'core_banking')}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Transaction isolation level (SERIALIZABLE for max safety)
    SQLALCHEMY_ENGINE_OPTIONS['isolation_level'] = 'REPEATABLE READ'
    
    # App settings
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
