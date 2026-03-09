import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from app.models import Transaction, Customer

# Global cache for the models in a real app these would be pre-trained and loaded via joblib/pickle
fraud_model = None
kmeans_model = None

def init_fraud_model():
    """Initialize mock anomaly detection for transactions."""
    global fraud_model
    # Using IsolationForest for unsupervised anomaly detection
    fraud_model = IsolationForest(contamination=0.01, random_state=42)
    # Generate mock training data
    np.random.seed(42)
    X = np.random.normal(loc=100, scale=500, size=(1000, 1)) # Amount
    X = np.append(X, np.random.normal(loc=12, scale=6, size=(1000, 1)), axis=1) # Hour of day
    fraud_model.fit(X)

def is_transaction_fraudulent(amount, hour_of_day):
    """Predict if a new transaction looks fraudulent."""
    global fraud_model
    if fraud_model is None:
        init_fraud_model()
    
    features = np.array([[amount, hour_of_day]])
    prediction = fraud_model.predict(features)
    # Isolation forest returns -1 for anomalies (fraud) and 1 for normal
    return bool(prediction[0] == -1)

def cluster_customers(customer_data):
    """Segment customers based on mock behavioral vectors."""
    global kmeans_model
    if not customer_data or len(customer_data) < 3:
        return {} # Not enough data
        
    kmeans_model = KMeans(n_clusters=3, random_state=42, n_init='auto')
    
    # customer_data expected as [[balance, rx_count, loan_amount], ...]
    clusters = kmeans_model.fit_predict(customer_data)
    return clusters.tolist()

def calculate_churn_risk(balance, inactivity_days):
    """Simple mock risk score calculation."""
    risk = 0.0
    if balance < 100:
        risk += 0.3
    if inactivity_days > 30:
        risk += 0.5
    if inactivity_days > 90:
        risk += 0.2
    return min(risk, 1.0)
