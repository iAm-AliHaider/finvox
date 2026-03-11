-- FinVox Database Schema
-- Neon Postgres, schema: finvox
-- Loans + Investment/Portfolio Management Company

CREATE SCHEMA IF NOT EXISTS finvox;
SET search_path TO finvox;

-- Relationship Managers
CREATE TABLE relationship_managers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    department TEXT DEFAULT 'wealth',
    portfolio_count INTEGER DEFAULT 0,
    aum_managed NUMERIC(15,2) DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customers
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT,
    national_id TEXT,
    date_of_birth DATE,
    address TEXT,
    city TEXT,
    country TEXT DEFAULT 'Saudi Arabia',
    kyc_status TEXT DEFAULT 'valid' CHECK (kyc_status IN ('valid','expired','pending','rejected')),
    kyc_expiry DATE,
    risk_profile TEXT DEFAULT 'moderate' CHECK (risk_profile IN ('conservative','moderate','aggressive','very_aggressive')),
    tier TEXT DEFAULT 'retail' CHECK (tier IN ('retail','premium','hnw','uhnw')),
    relationship_manager_id TEXT REFERENCES relationship_managers(id),
    preferred_language TEXT DEFAULT 'en',
    wa_verified BOOLEAN DEFAULT false,
    pin_hash TEXT,
    onboarded_at DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bank Accounts (customer linked)
CREATE TABLE bank_accounts (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    bank_name TEXT NOT NULL,
    account_no TEXT NOT NULL,
    iban TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    type TEXT NOT NULL CHECK (type IN ('national_id','income_proof','address_proof','tax_cert','bank_statement','contract','other')),
    name TEXT,
    file_url TEXT,
    verified BOOLEAN DEFAULT false,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Loans
CREATE TABLE loans (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    type TEXT NOT NULL CHECK (type IN ('personal','auto','home','business','education')),
    principal NUMERIC(15,2) NOT NULL,
    outstanding NUMERIC(15,2) NOT NULL,
    interest_rate NUMERIC(5,2) NOT NULL,
    tenure_months INTEGER NOT NULL,
    emi_amount NUMERIC(12,2) NOT NULL,
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active','closed','defaulted','restructured','pending')),
    collateral TEXT,
    purpose TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Loan Payments
CREATE TABLE loan_payments (
    id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL REFERENCES loans(id),
    due_date DATE NOT NULL,
    amount_due NUMERIC(12,2) NOT NULL,
    amount_paid NUMERIC(12,2) DEFAULT 0,
    paid_date DATE,
    status TEXT DEFAULT 'due' CHECK (status IN ('paid','due','overdue','partial','waived')),
    late_fee NUMERIC(8,2) DEFAULT 0,
    payment_method TEXT,
    reference_no TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Loan Applications
CREATE TABLE loan_applications (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    type TEXT NOT NULL,
    amount_requested NUMERIC(15,2) NOT NULL,
    tenure_requested INTEGER,
    purpose TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','docs_required','under_review','approved','rejected','disbursed')),
    assigned_to TEXT REFERENCES relationship_managers(id),
    notes TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Funds (investment products)
CREATE TABLE funds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('equity','debt','hybrid','money_market','real_estate','commodity','sukuk')),
    currency TEXT DEFAULT 'SAR',
    nav NUMERIC(12,4) NOT NULL,
    prev_nav NUMERIC(12,4),
    aum NUMERIC(18,2),
    risk_rating INTEGER CHECK (risk_rating BETWEEN 1 AND 5),
    return_1m NUMERIC(8,2),
    return_3m NUMERIC(8,2),
    return_1y NUMERIC(8,2),
    return_3y NUMERIC(8,2),
    return_5y NUMERIC(8,2),
    expense_ratio NUMERIC(5,2),
    min_investment NUMERIC(12,2) DEFAULT 1000,
    factsheet_url TEXT,
    active BOOLEAN DEFAULT true,
    nav_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolios
CREATE TABLE portfolios (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    name TEXT NOT NULL,
    type TEXT DEFAULT 'balanced' CHECK (type IN ('growth','balanced','conservative','custom','sharia_compliant')),
    total_invested NUMERIC(15,2) DEFAULT 0,
    current_value NUMERIC(15,2) DEFAULT 0,
    returns_pct NUMERIC(8,2) DEFAULT 0,
    risk_score INTEGER CHECK (risk_score BETWEEN 1 AND 10),
    benchmark TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Holdings (portfolio <-> fund)
CREATE TABLE holdings (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id),
    fund_id TEXT NOT NULL REFERENCES funds(id),
    units NUMERIC(15,4) NOT NULL,
    avg_buy_price NUMERIC(12,4) NOT NULL,
    current_nav NUMERIC(12,4),
    current_value NUMERIC(15,2),
    allocation_pct NUMERIC(5,2),
    unrealized_pnl NUMERIC(15,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions (buy/sell/switch/dividend)
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id),
    fund_id TEXT NOT NULL REFERENCES funds(id),
    type TEXT NOT NULL CHECK (type IN ('buy','sell','switch_in','switch_out','sip','dividend_reinvest')),
    units NUMERIC(15,4),
    price NUMERIC(12,4),
    amount NUMERIC(15,2) NOT NULL,
    fee NUMERIC(8,2) DEFAULT 0,
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending','completed','cancelled','failed')),
    reference_no TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- SIPs (Systematic Investment Plans)
CREATE TABLE sips (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id),
    fund_id TEXT NOT NULL REFERENCES funds(id),
    amount NUMERIC(12,2) NOT NULL,
    frequency TEXT DEFAULT 'monthly' CHECK (frequency IN ('monthly','quarterly','weekly')),
    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 28),
    status TEXT DEFAULT 'active' CHECK (status IN ('active','paused','stopped')),
    start_date DATE NOT NULL,
    next_date DATE,
    total_invested NUMERIC(15,2) DEFAULT 0,
    installments_done INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dividends
CREATE TABLE dividends (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id),
    fund_id TEXT NOT NULL REFERENCES funds(id),
    amount NUMERIC(12,2) NOT NULL,
    units_allotted NUMERIC(12,4),
    record_date DATE NOT NULL,
    payment_date DATE,
    reinvested BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Statements
CREATE TABLE statements (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    type TEXT NOT NULL CHECK (type IN ('account','tax','portfolio','loan','transaction')),
    period_start DATE,
    period_end DATE,
    file_url TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tickets (support)
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    category TEXT DEFAULT 'general' CHECK (category IN ('general','loan','investment','account','complaint','kyc','technical')),
    subject TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low','medium','high','urgent')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open','in_progress','resolved','closed','escalated')),
    assigned_to TEXT REFERENCES relationship_managers(id),
    resolution TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Interactions (call/chat log)
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    channel TEXT NOT NULL CHECK (channel IN ('voice','whatsapp','email','in_person','chat')),
    direction TEXT DEFAULT 'inbound' CHECK (direction IN ('inbound','outbound')),
    duration_seconds INTEGER,
    transcript TEXT,
    summary TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive','neutral','negative')),
    agent_actions JSONB DEFAULT '[]',
    tools_used JSONB DEFAULT '[]',
    verified BOOLEAN DEFAULT false,
    session_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Compliance Flags
CREATE TABLE compliance_flags (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    type TEXT NOT NULL CHECK (type IN ('kyc_expiry','aml_alert','risk_change','overdue_payment','document_missing','sanctions_hit')),
    details TEXT,
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open','investigating','resolved','dismissed')),
    flagged_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Notifications
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    message TEXT NOT NULL,
    channel TEXT DEFAULT 'whatsapp' CHECK (channel IN ('whatsapp','sms','email','push')),
    type TEXT DEFAULT 'info' CHECK (type IN ('info','alert','reminder','otp','summary')),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

-- OTP Store
CREATE TABLE otp_store (
    id SERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    code TEXT NOT NULL,
    purpose TEXT DEFAULT 'login' CHECK (purpose IN ('login','transaction','kyc','account_change')),
    attempts INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Trail
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    customer_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    details JSONB,
    ip_address TEXT,
    channel TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_loans_customer ON loans(customer_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loan_payments_loan ON loan_payments(loan_id);
CREATE INDEX idx_loan_payments_status ON loan_payments(status);
CREATE INDEX idx_portfolios_customer ON portfolios(customer_id);
CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX idx_sips_portfolio ON sips(portfolio_id);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_interactions_customer ON interactions(customer_id);
CREATE INDEX idx_otp_phone ON otp_store(phone);
CREATE INDEX idx_audit_customer ON audit_log(customer_id);
CREATE INDEX idx_compliance_customer ON compliance_flags(customer_id);
CREATE INDEX idx_notifications_customer ON notifications(customer_id);
