from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_message = 'Login required'
login_manager.login_message_category = 'warning'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # 🔥 CRITICAL: User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import AdminUser
        return AdminUser.query.get(int(user_id))
    
    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
