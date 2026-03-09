from flask import current_app, request
from app import db
from app.models import AdminUser, UserLog
from werkzeug.security import generate_password_hash
from functools import wraps
from flask_login import current_user
from flask import abort

def create_default_admin():
    with current_app.app_context():
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(
                username='admin',
                email='admin@bank.com',
                password_hash=generate_password_hash(current_app.config['ADMIN_PASSWORD'], method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Enterprise Admin created: admin / {current_app.config['ADMIN_PASSWORD']}")

def role_required(*roles):
    """Decorator to enforce role-based access control."""
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            # Admins can access manager/staff routes usually, but let's strictly check if their role is in the allowed roles
            # or if they are super admin
            if current_user.role not in roles and current_user.role != 'admin':
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def log_audit(action, details=None):
    """Helper to consistently log user actions."""
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
            # Determine if it's admin/manager or customer
            user_type = 'admin' if isinstance(current_user, AdminUser) else 'customer'
        else:
            user_id = None
            user_type = 'anonymous'

        log = UserLog(
            user_id=user_id,
            user_type=user_type,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to write audit log: {e}")
