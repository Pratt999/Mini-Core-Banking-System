from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='manager') # admin/manager/staff
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), nullable=False)
    branch_code = db.Column(db.String(20), unique=True)
    address = db.Column(db.Text)
    manager_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model, UserMixin): # Made customer a UserMixin for login
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    password_hash = db.Column(db.String(255)) # Added password for portal loging
    risk_score = db.Column(db.Float, default=0.0) # For ML Churn Prediction
    cluster_group = db.Column(db.Integer, nullable=True) # For ML Segmentation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='customer', lazy=True, cascade="all, delete-orphan")
    loans = db.relationship('Loan', backref='customer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        if not self.password_hash: return False
        return check_password_hash(self.password_hash, password)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD') # Multi-currency support
    account_type = db.Column(db.String(20), default='savings')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', 
                                   foreign_keys='Transaction.account_id',
                                   backref='account', 
                                   lazy=True, 
                                   cascade="all, delete-orphan")

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_reference = db.Column(db.String(50), unique=True, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    # target_account_id for internal transfers
    target_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True) 
    transaction_type = db.Column(db.String(20)) # deposit, withdrawal, transfer
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.Text)
    is_fraudulent = db.Column(db.Boolean, default=False) # AI Fraud detection flag
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    loan_reference = db.Column(db.String(50), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=8.5)
    tenure_months = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending') # pending, active, rejected, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    payments = db.relationship('LoanPayment', backref='loan', lazy=True, cascade="all, delete-orphan")

class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(50), unique=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')

class UserLog(db.Model):
    __tablename__ = 'user_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True) # ID of user/admin
    user_type = db.Column(db.String(20)) # 'admin' or 'customer'
    action = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
