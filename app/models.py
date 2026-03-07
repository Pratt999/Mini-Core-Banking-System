from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash

# 🔥 ADD THIS ADMIN MODEL FIRST
class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # ✅ NOT NULL
    password_hash = db.Column(db.String(255), nullable=False)       # 🔥 INCREASED 120→255
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), nullable=False)
    branch_code = db.Column(db.String(20), unique=True)
    address = db.Column(db.Text)
    manager_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='customer', lazy=True)
    loans = db.relationship('Loan', backref='customer', lazy=True)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    account_type = db.Column(db.String(20), default='savings')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    transaction_type = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=8.5)
    tenure_months = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 🔥 MISSING MODEL - ADD THIS
class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='paid')
