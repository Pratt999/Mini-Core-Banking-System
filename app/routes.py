from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from app.models import db, Branch, Customer, Account, Transaction, Loan, LoanPayment, AdminUser
from app.forms import LoginForm, CustomerForm, AccountForm, TransactionForm, LoanApplicationForm
from app.auth import role_required, log_audit
from app.banking_core import execute_transfer
from app.ml_models import is_transaction_fraudulent, cluster_customers, calculate_churn_risk
from app.celery_tasks import send_welcome_email, generate_monthly_statement, alert_fraud_suspicion
from app import socketio
import datetime
import os

main_bp = Blueprint('main', __name__)

# --- Authentication ---
@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if not user:
             # Try check if it's email login
             user = AdminUser.query.filter_by(email=form.username.data).first()
             
        if user and user.check_password(form.password.data):
             login_user(user)
             user.last_login_at = datetime.datetime.utcnow()
             db.session.commit()
             log_audit('LOGIN_SUCCESS')
             flash(f'Welcome back, {user.username}!', 'success')
             return redirect(url_for('main.dashboard'))
        else:
             log_audit('LOGIN_FAILED', f'Failed attempt for user: {form.username.data}')
             flash('Invalid credentials. Please check username/password.', 'danger')
             
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT')
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('main.login'))

# --- Dashboard ---
@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'customers': Customer.query.count(),
        'accounts': Account.query.count(),
        'loans_pending': Loan.query.filter_by(status='pending').count(),
        'total_balance': float(db.session.query(func.sum(Account.balance)).scalar() or 0)
    }
    recent_tx = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # ML Clustering mock logic for dashboard display
    all_customers = Customer.query.all()
    vectors = [[(c.accounts[0].balance if c.accounts else 0), len(c.accounts), len(c.loans)] for c in all_customers]
    clusters = cluster_customers(vectors)
    
    return render_template('dashboard.html', stats=stats, transactions=recent_tx)

# --- Customers ---
@main_bp.route('/customers')
@login_required
def customers():
    customers_list = Customer.query.order_by(Customer.created_at.desc()).all()
    # Mock Churn update dynamically
    for c in customers_list:
        total_bal = sum([a.balance for a in c.accounts])
        days = (datetime.datetime.utcnow() - c.created_at).days
        c.risk_score = calculate_churn_risk(total_bal, days)
        
    return render_template('customers.html', customers=customers_list)

@main_bp.route('/customer/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        try:
            # Generate unique ID
            cid = f"CUST{datetime.datetime.now().strftime('%y%m%d%H%M')}"
            
            customer = Customer(
                customer_id=cid,
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data
            )
            # Optional: set random portal password
            customer.set_password("changeme123")
            
            db.session.add(customer)
            db.session.commit()
            
            log_audit('CUSTOMER_CREATED', f"ID: {cid}")
            # Async Task: Send welcome email
            send_welcome_email.delay(customer.email, customer.name)
            
            flash(f'✅ Customer "{customer.name}" onboarded successfully! ID: {cid}', 'success')
            return redirect(url_for('main.customers'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error adding customer: {str(e)}', 'danger')
            
    return render_template('add_customer.html', form=form)

# --- Accounts ---
@main_bp.route('/accounts')
@login_required
def accounts():
    accounts_list = Account.query.join(Customer).order_by(Account.created_at.desc()).all()
    return render_template('accounts.html', accounts=accounts_list)

@main_bp.route('/account/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_account():
    form = AccountForm()
    # Populate customer choices dynamically
    form.customer_id.choices = [(c.id, f"{c.name} ({c.customer_id})") for c in Customer.query.all()]
    
    if form.validate_on_submit():
        try:
            acc_num = f"AC{datetime.datetime.now().strftime('%y%m%d%M%S')}"
            account = Account(
                account_number=acc_num,
                customer_id=form.customer_id.data,
                account_type=form.account_type.data,
                currency=form.currency.data,
                balance=form.initial_deposit.data
            )
            db.session.add(account)
            db.session.commit()
            
            log_audit('ACCOUNT_OPENED', f"Acc: {acc_num}")
            flash(f'✅ Account {acc_num} opened successfully!', 'success')
            return redirect(url_for('main.accounts'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error opening account: {str(e)}', 'danger')
            
    return render_template('add_account.html', form=form)

# --- Transactions (Deposit/Withdrawal/Transfer) ---
@main_bp.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    form = TransactionForm()
    # Populate account choices
    acc_choices = [(a.id, f"{a.account_number} ({a.balance} {a.currency})") for a in Account.query.filter_by(status='active').all()]
    form.account_id.choices = acc_choices
    form.target_account_id.choices = [(0, '-- None --')] + acc_choices
    
    recent_tx = Transaction.query.order_by(Transaction.timestamp.desc()).limit(20).all()
    
    if form.validate_on_submit():
         tx_type = form.transaction_type.data
         amount = form.amount.data
         acc_id = form.account_id.data
         desc = form.description.data
         
         # AI Fraud Check mock
         hour = datetime.datetime.now().hour
         is_fraud = is_transaction_fraudulent(amount, hour)
         
         if is_fraud:
             flash('⚠️ AI Warning: Transaction flagged as potentially fraudulent. Sent for review.', 'warning')
             alert_fraud_suspicion.delay(999) # Mock ID
             # We might block it or flag it, let's just flag it for the demo
             
         try:
             account = Account.query.get(acc_id)
             assert account, "Account not found"
             assert account.status == 'active', "Account inactive"
             
             if tx_type == 'deposit':
                 account.balance += amount
                 tx = Transaction(transaction_reference=f"DEP-{datetime.datetime.now().timestamp()}",
                                  account_id=account.id, transaction_type='deposit', amount=amount,
                                  currency=account.currency, description=desc, is_fraudulent=is_fraud)
                 db.session.add(tx)
                 
             elif tx_type == 'withdrawal':
                 assert account.balance >= amount, "Insufficient funds"
                 account.balance -= amount
                 tx = Transaction(transaction_reference=f"WDL-{datetime.datetime.now().timestamp()}",
                                  account_id=account.id, transaction_type='withdrawal', amount=amount,
                                  currency=account.currency, description=desc, is_fraudulent=is_fraud)
                 db.session.add(tx)
                 
             elif tx_type == 'transfer':
                 target_id = form.target_account_id.data
                 success, msg = execute_transfer(account.id, target_id, amount, desc)
                 if not success:
                     raise Exception(msg)
                 flash(f'✅ Transfer processed successfully (Ref: {msg})', 'success')
                 
             db.session.commit()
             log_audit('TRANSACTION', f"{tx_type.upper()} {amount} on Acc {account.id}")
             
             # Notify clients via WebSocket of balance update!
             socketio.emit('balance_update', {
                 'account_id': account.id,
                 'new_balance': account.balance,
                 'currency': account.currency
             })
             
             if tx_type != 'transfer':
                 flash(f'✅ {tx_type.capitalize()} of {amount} processed successfully!', 'success')
             return redirect(url_for('main.transactions'))
             
         except Exception as e:
             db.session.rollback()
             flash(f'❌ Transaction failed: {str(e)}', 'danger')
             
    return render_template('transactions.html', form=form, transactions=recent_tx)

# --- Loans ---
@main_bp.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    form = LoanApplicationForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.all()]
    
    if form.validate_on_submit():
        try:
             ref = f"LN-{datetime.datetime.now().strftime('%M%S')}"
             loan = Loan(
                 loan_reference=ref,
                 customer_id=form.customer_id.data,
                 loan_amount=form.amount.data,
                 tenure_months=form.tenure.data
             )
             db.session.add(loan)
             db.session.commit()
             log_audit('LOAN_APPLIED', f"Ref: {ref}")
             flash('✅ Loan application submitted for review!', 'success')
             return redirect(url_for('main.loans'))
        except Exception as e:
             db.session.rollback()
             flash(f'❌ Error: {str(e)}', 'danger')
             
    loans_list = Loan.query.order_by(Loan.created_at.desc()).all()
    return render_template('loans.html', form=form, loans=loans_list)

@main_bp.route('/loan/approve/<int:loan_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def approve_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'active'
    db.session.commit()
    log_audit('LOAN_APPROVED', f"Loan ID: {loan.id}")
    flash(f'✅ Loan {loan.loan_reference} has been approved.', 'success')
    return redirect(url_for('main.loans'))

# --- Reports & Async Tasks ---
@main_bp.route('/api/generate_report/<int:account_id>', methods=['POST'])
@login_required
def trigger_report(account_id):
    account = Account.query.get_or_404(account_id)
    # Trigger celery task
    task = generate_monthly_statement.delay(account.id, account.balance)
    return jsonify({"status": "processing", "task_id": task.id}), 202

@main_bp.route('/system/health')
@login_required
@role_required('admin')
def system_health():
    # Admin System Dashboard
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).limit(50).all()
    return render_template('system_health.html', logs=logs)
