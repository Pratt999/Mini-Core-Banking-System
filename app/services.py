import logging
from datetime import datetime, timedelta
from sqlalchemy import text, and_
from app.models import db, Account, Transaction, Loan, LoanPayment
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

logger = logging.getLogger(__name__)

class BankingService:
    MAX_TXN_AMOUNT = 1000000
    MAX_DAILY_TRANSFER = 5000000
    
    @staticmethod
    def create_unique_code(prefix, model_class):
        """Generate unique business codes"""
        while True:
            code = f"{prefix}{uuid.uuid4().hex[:6].upper()}"
            if not model_class.query.filter_by(customer_code=code).first():
                return code
    
    @staticmethod
    def safe_transfer(from_account_id, to_account_id, amount):
        """
        ACID-Compliant Transfer with SELECT FOR UPDATE locking
        Atomic: All or nothing
        Consistent: CHECK constraints enforced
        Isolated: REPEATABLE READ level
        Durable: WAL commit
        """
        if amount <= 0 or amount > BankingService.MAX_TXN_AMOUNT:
            return False, "Invalid amount"
        
        # Start transaction context
        try:
            # Lock both accounts (prevents lost updates)
            from_acct = db.session.query(Account).filter_by(
                account_id=from_account_id, status='ACTIVE'
            ).with_for_update().first()
            
            to_acct = db.session.query(Account).filter_by(
                account_id=to_account_id, status='ACTIVE'
            ).with_for_update().first()
            
            if not from_acct or not to_acct:
                return False, "Account not found or inactive"
            
            if from_acct.balance < amount:
                return False, "Insufficient balance"
            
            # Check daily limit
            today = datetime.now().date()
            daily_total = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.from_account_id == from_account_id,
                Transaction.txn_type == 'TRANSFER',
                func.date(Transaction.txn_timestamp) == today
            ).scalar() or 0
            
            if daily_total + amount > BankingService.MAX_DAILY_TRANSFER:
                return False, "Daily transfer limit exceeded"
            
            # BUSINESS LOGIC: Atomic updates
            from_acct.balance -= amount
            to_acct.balance += amount
            
            # Audit trail (immutable record)
            txn = Transaction(
                txn_ref=BankingService.create_unique_code('TXN', Transaction),
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                txn_type='TRANSFER',
                amount=amount,
                balance_after=from_acct.balance,  # Source account post-balance
                remarks=f"Transfer {amount} to account {to_account_id}"
            )
            
            db.session.add(txn)
            db.session.commit()  # ACID commit point
            
            logger.info(f"Transfer SUCCESS: {amount} from {from_account_id} to {to_account_id}")
            return True, "Transfer successful"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transfer FAILED: {str(e)}")
            return False, f"Transfer failed: {str(e)}"
    
    @staticmethod
    def deposit(account_id, amount):
        """Simple deposit - still ACID protected"""
        try:
            account = db.session.query(Account).filter_by(
                account_id=account_id, status='ACTIVE'
            ).with_for_update().first()
            
            if not account or amount <= 0:
                return False, "Invalid account or amount"
            
            account.balance += amount
            
            txn = Transaction(
                txn_ref=BankingService.create_unique_code('DEP', Transaction),
                to_account_id=account_id,
                txn_type='DEPOSIT',
                amount=amount,
                balance_after=account.balance,
                remarks='Cash deposit'
            )
            
            db.session.add(txn)
            db.session.commit()
            
            logger.info(f"Deposit SUCCESS: {amount} to {account_id}")
            return True, "Deposit successful"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Deposit failed: {str(e)}"
    
    @staticmethod
    def withdraw(account_id, amount):
        """Withdrawal with balance check"""
        try:
            account = db.session.query(Account).filter_by(
                account_id=account_id, status='ACTIVE'
            ).with_for_update().first()
            
            if not account or amount <= 0 or account.balance < amount:
                return False, "Insufficient balance or invalid amount"
            
            account.balance -= amount
            
            txn = Transaction(
                txn_ref=BankingService.create_unique_code('WDL', Transaction),
                from_account_id=account_id,
                txn_type='WITHDRAW',
                amount=amount,
                balance_after=account.balance,
                remarks='Cash withdrawal'
            )
            
            db.session.add(txn)
            db.session.commit()
            
            logger.info(f"Withdrawal SUCCESS: {amount} from {account_id}")
            return True, "Withdrawal successful"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Withdrawal failed: {str(e)}"
    
    @staticmethod
    def make_loan_payment(loan_id, account_id, amount):
        """Loan payment - complex multi-table ACID transaction"""
        try:
            loan = db.session.query(Loan).filter_by(loan_id=loan_id, status='ACTIVE').first()
            account = db.session.query(Account).filter_by(account_id=account_id, status='ACTIVE').with_for_update().first()
            
            if not loan or not account:
                return False, "Loan or account not found"
            
            if account.balance < amount:
                return False, "Insufficient account balance"
            
            # Debit account
            account.balance -= amount
            
            # Record payment
            payment = LoanPayment(
                loan_id=loan_id,
                account_id=account_id,
                payment_amount=amount,
                remarks='Regular EMI payment'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            logger.info(f"Loan payment SUCCESS: {amount} for loan {loan_id}")
            return True, "Payment successful"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Payment failed: {str(e)}"
