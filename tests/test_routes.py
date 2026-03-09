import pytest
from app import create_app, db
from app.models import AdminUser, Customer, Account
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False
    })
    
    with app.app_context():
        db.create_all()
        admin = AdminUser(username='admin', email='test@bank.com', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"NexusCore" in response.data

def test_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b"Sign In" in response.data # Redirects to login

def test_successful_admin_login(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Overview Dashboard" in response.data
    assert b"Total Assets Under Mgmt" in response.data

def test_customer_creation_requires_login(client):
    response = client.post('/customer/add', data={
        'name': 'Test User', 'email': 'test@example.com', 'phone': '555-1234', 'address': '123 Test St'
    }, follow_redirects=False)
    assert response.status_code == 302 # redirect to login
