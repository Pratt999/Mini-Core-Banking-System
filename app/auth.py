from flask import current_app
from app import db
from app.models import AdminUser
from werkzeug.security import generate_password_hash

def create_default_admin():
    with current_app.app_context():
        # Delete broken admin first
        AdminUser.query.filter_by(username='admin').delete()
        db.session.commit()
        
        # Check if admin exists
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(
                username='admin',
                email='admin@bank.com',           # ✅ FIXED
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')  # ✅ Short hash
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin created: admin/admin123")
        else:
            print("✅ Admin exists")
