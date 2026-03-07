from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models import db, Branch, Customer, Account, Transaction, Loan, LoanPayment
from datetime import datetime

main_bp = Blueprint('main', __name__)

# PUBLIC ROUTES
@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['logged_in'] = True
            session['username'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials. Use admin/admin123', 'error')
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.login'))

# PROTECTED ROUTES
@main_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    stats = {
        'customers': Customer.query.count(),
        'accounts': Account.query.count(),
        'branches': Branch.query.count(),
        'total_balance': float(db.session.query(db.func.sum(Account.balance)).scalar() or 0)
    }
    recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, customers=recent_customers, username=session.get('username'))

# 🔥 CUSTOMER CRUD - FULLY FUNCTIONAL
@main_bp.route('/customers')
def customers():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    customers_list = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=customers_list)

@main_bp.route('/customer/add', methods=['GET', 'POST'])
def add_customer():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        try:
            customer = Customer(
                customer_id=request.form['customer_id'],
                name=request.form['name'],
                email=request.form['email'],
                phone=request.form['phone'],
                address=request.form['address']
            )
            db.session.add(customer)
            db.session.commit()
            flash(f'✅ Customer "{customer.name}" added successfully! ID: {customer.customer_id}', 'success')
            return redirect(url_for('main.customers'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error adding customer: {str(e)}', 'error')
    
    return render_template('add_customer.html')

@main_bp.route('/customer/<int:id>/delete', methods=['POST'])
def customer_delete(id):  # Fixed name
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash(f'✅ Customer "{customer.name}" deleted successfully!', 'success')
    return redirect(url_for('main.customers'))

# 🔥 ACCOUNT CRUD
@main_bp.route('/accounts')
def accounts():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    accounts_list = Account.query.join(Customer).order_by(Account.created_at.desc()).all()
    customers = Customer.query.all()
    return render_template('accounts.html', accounts=accounts_list, customers=customers)

@main_bp.route('/account/add', methods=['GET', 'POST'])
def add_account():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    
    customers = Customer.query.all()
    if request.method == 'POST':
        try:
            account = Account(
                account_number=request.form['account_number'],
                customer_id=int(request.form['customer_id']),
                balance=float(request.form['balance'] or 0),
                account_type=request.form['account_type']
            )
            db.session.add(account)
            db.session.commit()
            flash(f'✅ Account {account.account_number} created for {account.customer.name}!', 'success')
            return redirect(url_for('main.accounts'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'error')
    
    return render_template('add_account.html', customers=customers)

# BRANCHES
@main_bp.route('/branches')
def branches():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    branches_list = Branch.query.all()
    return render_template('branches.html', branches=branches_list)

@main_bp.route('/api/stats')
def api_stats():
    stats = {
        'customers': Customer.query.count(),
        'accounts': Account.query.count(),
        'balance': float(db.session.query(db.func.sum(Account.balance)).scalar() or 0)
    }
    return jsonify(stats)
