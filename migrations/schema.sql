-- Create database with proper constraints and indexes

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Branches (Master data)
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_code VARCHAR(10) UNIQUE NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_branch_city (city)
);

-- Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (Savings/Current)
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    account_type VARCHAR(10) CHECK (account_type IN ('SAVINGS', 'CURRENT')) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00 CHECK (balance >= 0),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_account_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_account_branch FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

-- Transaction Log (All financial movements)
CREATE TABLE transactions (
    txn_id SERIAL PRIMARY KEY,
    txn_ref VARCHAR(30) UNIQUE NOT NULL,
    from_account_id INTEGER REFERENCES accounts(account_id) ON DELETE SET NULL,
    to_account_id INTEGER REFERENCES accounts(account_id) ON DELETE SET NULL,
    txn_type VARCHAR(20) NOT NULL CHECK (txn_type IN ('DEPOSIT', 'WITHDRAW', 'TRANSFER')),
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    balance_after DECIMAL(15,2) NOT NULL,
    txn_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'SUCCESS' CHECK (status IN ('SUCCESS', 'FAILED')),
    remarks TEXT,
    
    -- Indexes for fast lookups
    INDEX idx_txn_from_account (from_account_id, txn_timestamp DESC),
    INDEX idx_txn_to_account (to_account_id, txn_timestamp DESC),
    INDEX idx_txn_ref (txn_ref),
    INDEX idx_txn_type_time (txn_type, txn_timestamp DESC)
);

-- Loans
CREATE TABLE loans (
    loan_id SERIAL PRIMARY KEY,
    loan_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
    principal DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,2) NOT NULL,
    tenure_months INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED', 'DEFAULTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan Payments
CREATE TABLE loan_payments (
    payment_id SERIAL PRIMARY KEY,
    loan_id INTEGER NOT NULL REFERENCES loans(loan_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    payment_amount DECIMAL(15,2) NOT NULL CHECK (payment_amount > 0),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    
    INDEX idx_loan_payment_loan (loan_id, payment_date DESC)
);

-- Insert demo data
INSERT INTO branches (branch_code, branch_name, city) VALUES 
('MUM001', 'Mumbai Central', 'Mumbai'),
('DEL001', 'Delhi Main', 'Delhi'),
('BAN001', 'Bangalore Tech', 'Bangalore');

INSERT INTO customers (customer_code, name, email, phone) VALUES 
('CUST001', 'Rahul Sharma', 'rahul@bank.com', '9876543210'),
('CUST002', 'Priya Singh', 'priya@bank.com', '9876543211');
