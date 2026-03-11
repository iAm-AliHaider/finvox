"""FinVox Database Layer - All DB functions for voice agent tools."""
import asyncpg
import logging
import os
from datetime import datetime, timedelta, timezone
import random
import string

logger = logging.getLogger("finvox.db")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_laesRAW8Dui1@ep-plain-sound-aib5z9bz-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

_pool = None

async def _init_conn(conn):
    await conn.execute("SET search_path TO finvox")

async def get_pool():
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, init=_init_conn)
    return _pool

async def reset_pool():
    global _pool
    _pool = None


# â”€â”€â”€ Customer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_customer_by_phone(phone: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM finvox.customers WHERE phone = $1", phone
        )
        return dict(row) if row else None

async def get_customer(customer_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM finvox.customers WHERE id = $1", customer_id)
        return dict(row) if row else None

async def search_customer(query: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, name, phone, email, tier, kyc_status
               FROM finvox.customers
               WHERE name ILIKE $1 OR phone ILIKE $1 OR email ILIKE $1 OR national_id ILIKE $1
               LIMIT 10""",
            f"%{query}%"
        )
        return [dict(r) for r in rows]

async def update_customer_field(customer_id: str, field: str, value: str) -> bool:
    allowed = {"phone", "email", "address", "city", "preferred_language"}
    if field not in allowed:
        return False
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE finvox.customers SET {field} = $1 WHERE id = $2", value, customer_id
        )
        return True


async def create_customer(name: str, phone: str, email: str = None, national_id: str = None, city: str = None) -> dict:
    """Create a new customer account. Returns the new customer dict."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Generate next ID
        row = await conn.fetchrow(
            "SELECT id FROM finvox.customers ORDER BY created_at DESC LIMIT 1"
        )
        if row:
            num = int(row["id"].replace("CUST", "")) + 1
        else:
            num = 1
        new_id = f"CUST{num:03d}"

        await conn.execute(
            """INSERT INTO finvox.customers (id, name, phone, email, national_id, city, kyc_status, tier, preferred_language, wa_verified, onboarded_at, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, 'pending', 'retail', 'en', true, CURRENT_DATE, NOW())""",
            new_id, name, phone, email, national_id, city
        )
        return {"id": new_id, "name": name, "phone": phone, "email": email, "tier": "retail", "kyc_status": "pending"}



# â”€â”€â”€ OTP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def generate_otp(phone: str, purpose: str = "login") -> str:
    code = "".join(random.choices(string.digits, k=6))
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Invalidate old codes
        await conn.execute(
            "DELETE FROM finvox.otp_store WHERE phone = $1 AND purpose = $2", phone, purpose
        )
        await conn.execute(
            """INSERT INTO finvox.otp_store (phone, code, purpose, expires_at)
               VALUES ($1, $2, $3, $4)""",
            phone, code, purpose, expires
        )
    return code

async def verify_otp(phone: str, code: str, purpose: str = "login") -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM finvox.otp_store
               WHERE phone = $1 AND purpose = $2 AND verified = false
               ORDER BY created_at DESC LIMIT 1""",
            phone, purpose
        )
        if not row:
            return {"verified": False, "error": "No OTP found"}
        if row["attempts"] >= 3:
            return {"verified": False, "error": "Too many attempts, locked"}
        exp = row["expires_at"]
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            return {"verified": False, "error": "OTP expired"}
        if row["code"] != code:
            await conn.execute(
                "UPDATE finvox.otp_store SET attempts = attempts + 1 WHERE id = $1", row["id"]
            )
            return {"verified": False, "error": "Invalid code", "attempts_left": 2 - row["attempts"]}
        await conn.execute(
            "UPDATE finvox.otp_store SET verified = true WHERE id = $1", row["id"]
        )
        return {"verified": True}


# â”€â”€â”€ Loans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_customer_loans(customer_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT l.*, 
               (SELECT COUNT(*) FROM finvox.loan_payments WHERE loan_id = l.id AND status = 'overdue') as overdue_count
               FROM finvox.loans l WHERE l.customer_id = $1 ORDER BY l.start_date DESC""",
            customer_id
        )
        return [dict(r) for r in rows]

async def get_loan_detail(loan_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        loan = await conn.fetchrow("SELECT * FROM finvox.loans WHERE id = $1", loan_id)
        if not loan:
            return None
        payments = await conn.fetch(
            """SELECT * FROM finvox.loan_payments WHERE loan_id = $1
               ORDER BY due_date DESC LIMIT 12""", loan_id
        )
        return {"loan": dict(loan), "payments": [dict(p) for p in payments]}

async def get_payment_history(loan_id: str, limit: int = 12) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM finvox.loan_payments WHERE loan_id = $1 ORDER BY due_date DESC LIMIT $2",
            loan_id, limit
        )
        return [dict(r) for r in rows]

async def get_next_emi(loan_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM finvox.loan_payments
               WHERE loan_id = $1 AND status IN ('due','overdue')
               ORDER BY due_date ASC LIMIT 1""",
            loan_id
        )
        return dict(row) if row else None

async def calculate_prepayment(loan_id: str, amount: float) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        loan = await conn.fetchrow("SELECT * FROM finvox.loans WHERE id = $1", loan_id)
        if not loan:
            return {"error": "Loan not found"}
        outstanding = float(loan["outstanding"])
        rate = float(loan["interest_rate"])
        if amount > outstanding:
            amount = outstanding
        new_outstanding = outstanding - amount
        # Rough savings calc
        monthly_rate = rate / 100 / 12
        if monthly_rate > 0 and new_outstanding > 0:
            remaining_months = new_outstanding / float(loan["emi_amount"])
            interest_saved = amount * monthly_rate * remaining_months
        else:
            interest_saved = 0
        return {
            "current_outstanding": outstanding,
            "prepayment_amount": amount,
            "new_outstanding": new_outstanding,
            "estimated_interest_saved": round(interest_saved, 2),
            "prepayment_penalty": 0,  # Assume no penalty
        }

async def get_loan_applications(customer_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM finvox.loan_applications WHERE customer_id = $1 ORDER BY submitted_at DESC",
            customer_id
        )
        return [dict(r) for r in rows]

async def get_overdue_summary(customer_id: str = None) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if customer_id:
            rows = await conn.fetch(
                """SELECT lp.*, l.type as loan_type, c.name as customer_name
                   FROM finvox.loan_payments lp
                   JOIN finvox.loans l ON lp.loan_id = l.id
                   JOIN finvox.customers c ON l.customer_id = c.id
                   WHERE l.customer_id = $1 AND lp.status = 'overdue'
                   ORDER BY lp.due_date""",
                customer_id
            )
        else:
            rows = await conn.fetch(
                """SELECT lp.*, l.type as loan_type, c.name as customer_name, c.phone
                   FROM finvox.loan_payments lp
                   JOIN finvox.loans l ON lp.loan_id = l.id
                   JOIN finvox.customers c ON l.customer_id = c.id
                   WHERE lp.status = 'overdue'
                   ORDER BY lp.due_date"""
            )
        return [dict(r) for r in rows]


# â”€â”€â”€ Portfolios & Investments â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_customer_portfolios(customer_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM finvox.portfolios WHERE customer_id = $1", customer_id
        )
        return [dict(r) for r in rows]

async def get_portfolio_detail(portfolio_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        portfolio = await conn.fetchrow("SELECT * FROM finvox.portfolios WHERE id = $1", portfolio_id)
        if not portfolio:
            return None
        holdings = await conn.fetch(
            """SELECT h.*, f.name as fund_name, f.category, f.risk_rating,
                      f.return_1y, f.return_3y
               FROM finvox.holdings h JOIN finvox.funds f ON h.fund_id = f.id
               WHERE h.portfolio_id = $1
               ORDER BY h.current_value DESC""",
            portfolio_id
        )
        return {"portfolio": dict(portfolio), "holdings": [dict(h) for h in holdings]}

async def get_holdings(portfolio_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT h.*, f.name as fund_name, f.category, f.nav as latest_nav,
                      f.risk_rating, f.return_1y
               FROM finvox.holdings h JOIN finvox.funds f ON h.fund_id = f.id
               WHERE h.portfolio_id = $1
               ORDER BY h.current_value DESC""",
            portfolio_id
        )
        return [dict(r) for r in rows]

async def get_fund_info(fund_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM finvox.funds WHERE id = $1", fund_id)
        return dict(row) if row else None

async def search_funds(query: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, name, category, nav, risk_rating, return_1y, return_3y
               FROM finvox.funds WHERE name ILIKE $1 OR category ILIKE $1
               ORDER BY return_1y DESC NULLS LAST LIMIT 10""",
            f"%{query}%"
        )
        return [dict(r) for r in rows]

async def get_transactions(portfolio_id: str, limit: int = 20) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT t.*, f.name as fund_name
               FROM finvox.transactions t JOIN finvox.funds f ON t.fund_id = f.id
               WHERE t.portfolio_id = $1
               ORDER BY t.executed_at DESC LIMIT $2""",
            portfolio_id, limit
        )
        return [dict(r) for r in rows]

async def get_sips(portfolio_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT s.*, f.name as fund_name
               FROM finvox.sips s JOIN finvox.funds f ON s.fund_id = f.id
               WHERE s.portfolio_id = $1
               ORDER BY s.status, s.next_date""",
            portfolio_id
        )
        return [dict(r) for r in rows]

async def get_dividends(portfolio_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT d.*, f.name as fund_name
               FROM finvox.dividends d JOIN finvox.funds f ON d.fund_id = f.id
               WHERE d.portfolio_id = $1
               ORDER BY d.record_date DESC""",
            portfolio_id
        )
        return [dict(r) for r in rows]

async def get_portfolio_summary(customer_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM finvox.portfolios WHERE customer_id = $1", customer_id
        )
        portfolios = [dict(r) for r in rows]
        total_invested = sum(float(p.get("total_invested", 0)) for p in portfolios)
        current_value = sum(float(p.get("current_value", 0)) for p in portfolios)
        returns_pct = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        
        # Get allocation breakdown
        allocation = await conn.fetch(
            """SELECT f.category, SUM(h.current_value) as total_value
               FROM finvox.holdings h
               JOIN finvox.funds f ON h.fund_id = f.id
               JOIN finvox.portfolios p ON h.portfolio_id = p.id
               WHERE p.customer_id = $1
               GROUP BY f.category
               ORDER BY total_value DESC""",
            customer_id
        )
        return {
            "total_invested": total_invested,
            "current_value": current_value,
            "total_returns": current_value - total_invested,
            "returns_pct": round(returns_pct, 1),
            "portfolio_count": len(portfolios),
            "portfolios": portfolios,
            "allocation": [dict(a) for a in allocation],
        }


# â”€â”€â”€ Tickets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def create_ticket(customer_id: str, category: str, subject: str, description: str = "",
                        priority: str = "medium") -> dict:
    ticket_id = f"TK{random.randint(100,999)}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO finvox.tickets (id, customer_id, category, subject, description, priority)
               VALUES ($1,$2,$3,$4,$5,$6)""",
            ticket_id, customer_id, category, subject, description, priority
        )
    return {"id": ticket_id, "status": "open"}

async def get_customer_tickets(customer_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM finvox.tickets WHERE customer_id = $1 ORDER BY created_at DESC",
            customer_id
        )
        return [dict(r) for r in rows]


# â”€â”€â”€ Interactions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def log_interaction(customer_id: str, channel: str, duration: int = None,
                          transcript: str = None, summary: str = None,
                          sentiment: str = None, tools_used: list = None,
                          session_id: str = None) -> str:
    int_id = f"INT{random.randint(1000,9999)}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        import json
        await conn.execute(
            """INSERT INTO finvox.interactions (id, customer_id, channel, duration_seconds,
               transcript, summary, sentiment, tools_used, verified, session_id)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
            int_id, customer_id, channel, duration, transcript, summary,
            sentiment, json.dumps(tools_used or []), True, session_id
        )
    return int_id


# â”€â”€â”€ Compliance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_compliance_flags(customer_id: str = None) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if customer_id:
            rows = await conn.fetch(
                """SELECT cf.*, c.name as customer_name
                   FROM finvox.compliance_flags cf JOIN finvox.customers c ON cf.customer_id = c.id
                   WHERE cf.customer_id = $1 AND cf.status != 'resolved'
                   ORDER BY cf.flagged_at DESC""",
                customer_id
            )
        else:
            rows = await conn.fetch(
                """SELECT cf.*, c.name as customer_name, c.phone
                   FROM finvox.compliance_flags cf JOIN finvox.customers c ON cf.customer_id = c.id
                   WHERE cf.status != 'resolved'
                   ORDER BY cf.severity DESC, cf.flagged_at DESC"""
            )
        return [dict(r) for r in rows]


# â”€â”€â”€ Audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def log_audit(customer_id: str, actor: str, action: str,
                    entity_type: str = None, entity_id: str = None,
                    details: dict = None, channel: str = "voice"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        import json
        await conn.execute(
            """INSERT INTO finvox.audit_log (customer_id, actor, action, entity_type, entity_id, details, channel)
               VALUES ($1,$2,$3,$4,$5,$6,$7)""",
            customer_id, actor, action, entity_type, entity_id,
            json.dumps(details) if details else None, channel
        )


# â”€â”€â”€ Notifications â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def create_notification(customer_id: str, message: str,
                              channel: str = "whatsapp", ntype: str = "info") -> str:
    notif_id = f"N{random.randint(10000,99999)}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO finvox.notifications (id, customer_id, message, channel, type)
               VALUES ($1,$2,$3,$4,$5)""",
            notif_id, customer_id, message, channel, ntype
        )
    return notif_id


# â”€â”€â”€ Employee / RM Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def get_rm_portfolio(rm_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rm = await conn.fetchrow("SELECT * FROM finvox.relationship_managers WHERE id = $1", rm_id)
        if not rm:
            return None
        customers = await conn.fetch(
            """SELECT c.id, c.name, c.phone, c.tier,
               (SELECT COUNT(*) FROM finvox.loans WHERE customer_id = c.id AND status = 'active') as active_loans,
               (SELECT SUM(current_value) FROM finvox.portfolios WHERE customer_id = c.id) as total_aum
               FROM finvox.customers c WHERE c.relationship_manager_id = $1
               ORDER BY total_aum DESC NULLS LAST""",
            rm_id
        )
        return {"rm": dict(rm), "customers": [dict(c) for c in customers]}

async def get_daily_collections() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        today = datetime.now(timezone.utc).date()
        due_today = await conn.fetch(
            """SELECT lp.*, l.type as loan_type, c.name as customer_name
               FROM finvox.loan_payments lp
               JOIN finvox.loans l ON lp.loan_id = l.id
               JOIN finvox.customers c ON l.customer_id = c.id
               WHERE lp.due_date = $1""",
            today
        )
        total_due = sum(float(r["amount_due"]) for r in due_today)
        total_collected = sum(float(r["amount_paid"]) for r in due_today)
        return {
            "date": str(today),
            "payments_due": len(due_today),
            "total_due": total_due,
            "total_collected": total_collected,
            "collection_rate": round(total_collected / total_due * 100, 1) if total_due > 0 else 0,
            "details": [dict(r) for r in due_today]
        }



