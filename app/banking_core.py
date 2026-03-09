import random
import uuid
import datetime
import requests
from app.models import db, Account, Transaction

def generate_reference(prefix="TRX"):
    """Generate unique transaction reference"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{timestamp}-{random_str}"

def convert_currency(amount, from_currency, to_currency):
    """
    Mock currency conversion.
    In a real app, you would integrate a free API like Fixer.io or ExchangeRate-API.
    """
    if from_currency == to_currency:
        return amount
        
    # Mock rates relative to USD
    rates = {
        'USD': 1.0,
        'EUR': 0.92,
        'INR': 83.5,
        'GBP': 0.79
    }
    
    # Convert to USD first, then to target
    amount_in_usd = amount / rates.get(from_currency, 1.0)
    converted_amount = amount_in_usd * rates.get(to_currency, 1.0)
    return round(converted_amount, 2)

def execute_transfer(sender_account_id, receiver_account_id, amount, description=""):
    """
    Execute a secure transfer between two accounts with ACID properties.
    """
    try:
        sender = Account.query.get(sender_account_id)
        receiver = Account.query.get(receiver_account_id)
        
        if not sender or not receiver:
            return False, "Invalid account details."
            
        if sender.status != 'active' or receiver.status != 'active':
            return False, "One of the accounts is inactive."
            
        if sender.balance < amount:
            return False, "Insufficient funds."
            
        # Convert amount if currencies differ
        actual_amount_received = convert_currency(amount, sender.currency, receiver.currency)
        
        # Deduct from sender
        sender.balance -= amount
        # Add to receiver
        receiver.balance += actual_amount_received
        
        reference = generate_reference("TRF")
        tx = Transaction(
            transaction_reference=reference,
            account_id=sender.id,
            target_account_id=receiver.id,
            transaction_type="transfer",
            amount=amount,
            currency=sender.currency,
            description=description
        )
        
        db.session.add(tx)
        
        # We rely on PostgreSQL's REPEATABLE READ isolation to prevent race conditions during the commit
        db.session.commit()
        return True, reference
    except Exception as e:
        db.session.rollback()
        return False, str(e)
