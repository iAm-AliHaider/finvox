"""Seed rich data for Ali Haider (C099) in MRNA."""
import asyncio
import sys
sys.path.insert(0, ".")
from database import get_pool

CID = "C099"
PHONE = "+966534006682"


async def main():
    pool = await get_pool()

    # Upsert customer
    exists = await pool.fetchrow("SELECT id FROM finvox.customers WHERE id=$1", CID)
    if exists:
        await pool.execute(
            "UPDATE finvox.customers SET name='Ali Haider',phone=$2,email='ali.haider@gmail.com',"
            "national_id='2099887766',date_of_birth='1995-06-15',address='Villa 7, Al-Hamra District',"
            "city='Riyadh',country='SA',tier='premium',kyc_status='valid',risk_profile='moderate',"
            "preferred_language='en',relationship_manager_id='RM001',wa_verified=true WHERE id=$1", CID, PHONE)
    else:
        await pool.execute(
            "INSERT INTO finvox.customers (id,name,phone,email,national_id,date_of_birth,address,city,country,tier,kyc_status,risk_profile,preferred_language,relationship_manager_id,wa_verified) "
            "VALUES ($1,'Ali Haider',$2,'ali.haider@gmail.com','2099887766','1995-06-15','Villa 7, Al-Hamra District','Riyadh','SA','premium','valid','moderate','en','RM001',true)", CID, PHONE)
    print(f"Customer {CID} ready")

    # Clean
    await pool.execute("DELETE FROM finvox.loan_payments WHERE loan_id IN (SELECT id FROM finvox.loans WHERE customer_id=$1)", CID)
    for t in ["loans","loan_applications","tickets","compliance_flags","interactions"]:
        await pool.execute(f"DELETE FROM finvox.{t} WHERE customer_id=$1", CID)
    for t in ["dividends","transactions","sips","holdings"]:
        await pool.execute(f"DELETE FROM finvox.{t} WHERE portfolio_id IN (SELECT id FROM finvox.portfolios WHERE customer_id=$1)", CID)
    await pool.execute("DELETE FROM finvox.portfolios WHERE customer_id=$1", CID)
    print("  Cleaned old data")

    # === LOANS (type: personal|auto|home|business|education) ===
    await pool.execute(
        "INSERT INTO finvox.loans VALUES('L099A',$1,'home',850000,612000,4.25,240,5312.50,'2023-01-15','2043-01-15','active','Villa 7 Riyadh','Primary residence',NOW())", CID)
    await pool.execute(
        "INSERT INTO finvox.loans VALUES('L099B',$1,'auto',180000,132000,5.50,60,3435,'2024-06-01','2029-06-01','active','2024 Land Cruiser','Vehicle',NOW())", CID)
    await pool.execute(
        "INSERT INTO finvox.loans VALUES('L099C',$1,'personal',50000,0,8.00,24,2264,'2024-01-01','2025-12-31','closed',NULL,'Renovation',NOW())", CID)

    # Loan payments - use SQL date literals
    lp_sql = "INSERT INTO finvox.loan_payments (id,loan_id,due_date,amount_due,amount_paid,paid_date,status) VALUES "
    lp_rows = [
        "('LP099A1','L099A','2025-10-15',5312.50,5312.50,'2025-10-15','paid')",
        "('LP099A2','L099A','2025-11-15',5312.50,5312.50,'2025-11-15','paid')",
        "('LP099A3','L099A','2025-12-15',5312.50,5312.50,'2025-12-15','paid')",
        "('LP099A4','L099A','2026-01-15',5312.50,5312.50,'2026-01-15','paid')",
        "('LP099A5','L099A','2026-02-15',5312.50,5312.50,'2026-02-15','paid')",
        "('LP099A6','L099A','2026-03-15',5312.50,NULL,NULL,'due')",
        "('LP099B0','L099B','2025-12-01',3435,NULL,NULL,'overdue')",
        "('LP099B1','L099B','2026-01-01',3435,3435,'2026-01-02','paid')",
        "('LP099B2','L099B','2026-02-01',3435,3435,'2026-02-01','paid')",
        "('LP099B3','L099B','2026-03-01',3435,NULL,NULL,'due')",
    ]
    await pool.execute(lp_sql + ",".join(lp_rows))

    # Loan application
    await pool.execute(
        "INSERT INTO finvox.loan_applications (id,customer_id,type,amount_requested,tenure_requested,purpose,status,notes) "
        "VALUES('LA099A',$1,'business',500000,60,'AI consultancy expansion','under_review','Tech startup - MiddleMind AI')", CID)
    print("  3 loans + 10 payments + 1 application")

    # === PORTFOLIOS ===
    await pool.execute(
        "INSERT INTO finvox.portfolios VALUES('P099A',$1,'Growth Portfolio','growth',750000,892000,18.93,8,'TASI',NOW())", CID)
    await pool.execute(
        "INSERT INTO finvox.portfolios VALUES('P099B',$1,'Retirement Fund','balanced',300000,345000,15.00,5,'MSCI SA',NOW())", CID)
    await pool.execute(
        "INSERT INTO finvox.portfolios VALUES('P099C',$1,'Emergency Reserve','conservative',120000,125000,4.17,2,'SAIBOR',NOW())", CID)

    # === FUNDS ===
    funds_sql = """
    INSERT INTO finvox.funds (id,name,category,currency,nav,prev_nav,aum,risk_rating,return_1m,return_3m,return_1y,return_3y,return_5y,expense_ratio,min_investment,active) VALUES
    ('F001','Al-Rajhi Saudi Equity','equity','SAR',142.50,140.80,2500000000,4,1.2,3.8,12.5,38.2,65.0,1.5,5000,true),
    ('F002','HSBC Multi-Asset','hybrid','SAR',108.30,107.10,800000000,3,0.8,2.5,8.3,22.5,40.0,1.2,10000,true),
    ('F003','Riyad Money Market','money_market','SAR',25.10,25.05,3500000000,1,0.3,0.9,3.8,11.0,18.5,0.5,1000,true),
    ('F004','NCB Global Tech','equity','USD',285.00,278.50,1200000000,5,2.5,7.2,22.1,55.0,120.0,1.8,25000,true),
    ('F005','Jadwa Sukuk','sukuk','SAR',52.40,52.00,1800000000,2,0.4,1.3,5.2,16.0,28.0,0.8,5000,true),
    ('F006','Fransi Real Estate','real_estate','SAR',78.60,77.20,600000000,4,0.7,2.1,9.7,30.0,52.0,1.4,50000,true)
    ON CONFLICT (id) DO UPDATE SET nav=EXCLUDED.nav, prev_nav=EXCLUDED.prev_nav
    """
    await pool.execute(funds_sql)

    # === HOLDINGS ===
    await pool.execute("""INSERT INTO finvox.holdings (id,portfolio_id,fund_id,units,avg_buy_price,current_nav,current_value,allocation_pct,unrealized_pnl) VALUES
    ('H099A1','P099A','F001',3500,107.14,142.50,498750,55.9,124250),
    ('H099A2','P099A','F004',1200,208.33,285.00,342000,38.4,92000),
    ('H099A3','P099A','F006',800,63.75,78.60,62880,7.0,11880),
    ('H099B1','P099B','F002',2000,78.26,108.30,216600,62.8,60000),
    ('H099B2','P099B','F005',1500,85.33,52.40,78600,22.8,-50000),
    ('H099C1','P099C','F003',5000,24.00,25.10,125500,100.0,5500)""")

    # === SIPs ===
    await pool.execute("""INSERT INTO finvox.sips (id,portfolio_id,fund_id,amount,frequency,day_of_month,status,start_date,next_date,total_invested,installments_done) VALUES
    ('S099A','P099A','F001',5000,'monthly',15,'active','2023-07-01','2026-04-15',165000,33),
    ('S099B','P099B','F002',3000,'monthly',1,'active','2022-02-01','2026-04-01',147000,49),
    ('S099C','P099C','F003',2000,'monthly',5,'active','2024-04-01','2026-04-05',46000,23)""")
    print("  3 portfolios + 6 funds + 6 holdings + 3 SIPs")

    # === TRANSACTIONS (type: buy|sell|switch_in|switch_out|sip) ===
    await pool.execute("""INSERT INTO finvox.transactions (id,portfolio_id,fund_id,type,units,price,amount,fee,status,reference_no,executed_at) VALUES
    ('T099_1','P099A','F001','buy',420,119.05,50000,75,'completed','TXN-20260215A','2026-02-15'),
    ('T099_2','P099A','F004','buy',250,120.00,30000,45,'completed','TXN-20260120A','2026-01-20'),
    ('T099_3','P099B','F002','buy',150,100.00,15000,22,'completed','TXN-20260301A','2026-03-01'),
    ('T099_4','P099A','F006','sell',160,125.00,20000,30,'completed','TXN-20260228A','2026-02-28'),
    ('T099_5','P099B','F005','buy',100,100.00,10000,15,'completed','TXN-20251215A','2025-12-15'),
    ('T099_6','P099C','F003','buy',400,25.00,10000,5,'completed','TXN-20260105A','2026-01-05'),
    ('T099_7','P099A','F001','sip',42,119.05,5000,7,'completed','TXN-20260305A','2026-03-05'),
    ('T099_8','P099A','F004','switch_out',200,125.00,25000,37,'completed','TXN-20260210A','2026-02-10')""")
    print("  8 transactions")

    # === DIVIDENDS ===
    await pool.execute("""INSERT INTO finvox.dividends (id,portfolio_id,fund_id,amount,units_allotted,record_date,payment_date,reinvested) VALUES
    ('D099_1','P099A','F001',8500,60,'2025-12-20','2025-12-31',true),
    ('D099_2','P099A','F004',12000,42,'2025-12-20','2025-12-31',true),
    ('D099_3','P099B','F002',4200,39,'2025-12-20','2025-12-31',true),
    ('D099_4','P099B','F005',3100,59,'2026-02-20','2026-03-01',true),
    ('D099_5','P099C','F003',1800,72,'2026-01-10','2026-01-15',false)""")
    print("  5 dividends (SAR 29,600)")

    # === TICKETS ===
    await pool.execute("""INSERT INTO finvox.tickets (id,customer_id,category,subject,description,priority,status) VALUES
    ('TK099_1',$1,'loan','Home loan EMI reschedule','Want EMI date moved from 15th to 25th','high','open'),
    ('TK099_2',$1,'investment','Portfolio rebalancing','Shift 20%% equity to sukuk','medium','in_progress'),
    ('TK099_3',$1,'account','Address update done','Updated to Villa 7 Al-Hamra','low','resolved'),
    ('TK099_4',$1,'complaint','Auto loan early settlement','Need early settlement amount for L099B','high','open'),
    ('TK099_5',$1,'technical','Mobile app login issue','Cannot login after password reset','medium','resolved')""", CID)
    print("  5 tickets")

    # === COMPLIANCE (type: kyc_expiry|risk_change|overdue_payment) ===
    await pool.execute("""INSERT INTO finvox.compliance_flags (id,customer_id,type,details,severity,status) VALUES
    ('CF099_1',$1,'kyc_expiry','Annual KYC review due in 60 days','medium','open'),
    ('CF099_2',$1,'overdue_payment','Auto loan Dec 2025 payment overdue','high','investigating'),
    ('CF099_3',$1,'risk_change','SAR 50K+ transaction flagged','low','resolved')""", CID)
    print("  3 compliance flags")

    # === INTERACTIONS ===
    await pool.execute("""INSERT INTO finvox.interactions (id,customer_id,channel,direction,duration_seconds,summary,sentiment,verified) VALUES
    ('IX099_1',$1,'voice','inbound',245,'Home loan prepayment inquiry. 1%% fee explained.','positive',true),
    ('IX099_2',$1,'voice','inbound',180,'Auto loan overdue. Promised payment in 48h.','neutral',true),
    ('IX099_3',$1,'whatsapp','inbound',60,'Portfolio statement for tax filing. Sent via WA.','positive',true),
    ('IX099_4',$1,'voice','inbound',320,'Business loan status. Under credit review.','neutral',true),
    ('IX099_5',$1,'whatsapp','inbound',45,'SIP increase: Growth 3K to 5K.','positive',true),
    ('IX099_6',$1,'voice','inbound',190,'Routine check. Happy with returns.','positive',true)""", CID)
    print("  6 interactions")

    print(f"\nAli Haider ({CID}) fully seeded:")
    print(f"  Premium | KYC valid | Riyadh | RM001")
    print(f"  Loans: Home 850K + Auto 180K + Personal 50K (closed) + Business 500K (pending)")
    print(f"  Portfolios: Growth 892K + Retirement 345K + Emergency 125K = SAR 1.36M")
    print(f"  SIPs: 10K/mo (3 active) | Dividends: 29.6K")
    print(f"  1 overdue payment | 2 open tickets | 3 compliance flags")

    await pool.close()

asyncio.run(main())
