"""FinVox Natural Language to SQL - GPT-4o-mini powered."""
import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger("finvox.nl2sql")

SCHEMA_CONTEXT = """
Schema: finvox

Tables:
- customers(id, name, phone, email, national_id, date_of_birth, address, city, country, kyc_status, kyc_expiry, risk_profile, tier, relationship_manager_id, preferred_language, wa_verified, onboarded_at)
- relationship_managers(id, name, phone, email, department, portfolio_count, aum_managed, active)
- bank_accounts(id, customer_id, bank_name, account_no, iban, is_primary)
- loans(id, customer_id, type[personal/auto/home/business/education], principal, outstanding, interest_rate, tenure_months, emi_amount, start_date, maturity_date, status[active/closed/defaulted/restructured], collateral, purpose)
- loan_payments(id, loan_id, due_date, amount_due, amount_paid, paid_date, status[paid/due/overdue/partial/waived], late_fee, payment_method, reference_no)
- loan_applications(id, customer_id, type, amount_requested, tenure_requested, purpose, status[pending/docs_required/under_review/approved/rejected/disbursed], assigned_to, notes)
- funds(id, name, category[equity/debt/hybrid/money_market/real_estate/commodity/sukuk], currency, nav, aum, risk_rating[1-5], return_1m, return_3m, return_1y, return_3y, return_5y, expense_ratio, min_investment)
- portfolios(id, customer_id, name, type[growth/balanced/conservative/custom/sharia_compliant], total_invested, current_value, returns_pct, risk_score[1-10])
- holdings(id, portfolio_id, fund_id, units, avg_buy_price, current_nav, current_value, allocation_pct, unrealized_pnl)
- transactions(id, portfolio_id, fund_id, type[buy/sell/switch_in/switch_out/sip/dividend_reinvest], units, price, amount, fee, status, reference_no, executed_at)
- sips(id, portfolio_id, fund_id, amount, frequency[monthly/quarterly/weekly], day_of_month, status[active/paused/stopped], start_date, next_date, total_invested, installments_done)
- dividends(id, portfolio_id, fund_id, amount, units_allotted, record_date, payment_date, reinvested)
- tickets(id, customer_id, category, subject, description, priority, status[open/in_progress/resolved/closed/escalated], assigned_to, resolution)
- interactions(id, customer_id, channel[voice/whatsapp/email], direction, duration_seconds, transcript, summary, sentiment[positive/neutral/negative], tools_used, session_id, created_at)
- compliance_flags(id, customer_id, type, details, severity[low/medium/high/critical], status[open/investigating/resolved/dismissed])
- notifications(id, customer_id, message, channel, type[info/alert/reminder/otp/summary], sent_at)
- audit_log(id, customer_id, actor, action, entity_type, entity_id, details, channel, created_at)
"""

FEW_SHOT_EXAMPLES = """
Q: How many active loans do we have?
SQL: SELECT COUNT(*) as active_loans FROM finvox.loans WHERE status = 'active'

Q: What is Faisal's total outstanding loan balance?
SQL: SELECT SUM(l.outstanding) as total_outstanding FROM finvox.loans l JOIN finvox.customers c ON l.customer_id = c.id WHERE c.name ILIKE '%Faisal%' AND l.status = 'active'

Q: Which customers have overdue payments?
SQL: SELECT DISTINCT c.name, c.phone, COUNT(lp.id) as overdue_count, SUM(lp.amount_due - lp.amount_paid) as total_overdue FROM finvox.loan_payments lp JOIN finvox.loans l ON lp.loan_id = l.id JOIN finvox.customers c ON l.customer_id = c.id WHERE lp.status = 'overdue' GROUP BY c.name, c.phone ORDER BY total_overdue DESC

Q: What are the best performing funds this year?
SQL: SELECT name, category, nav, return_1y, risk_rating FROM finvox.funds WHERE active = true ORDER BY return_1y DESC NULLS LAST LIMIT 5

Q: What is my total portfolio value?
SQL: SELECT SUM(current_value) as total_value, SUM(total_invested) as total_invested, ROUND(((SUM(current_value) - SUM(total_invested)) / NULLIF(SUM(total_invested), 0) * 100)::numeric, 1) as returns_pct FROM finvox.portfolios WHERE customer_id = '{customer_id}'

Q: Show me all SIPs
SQL: SELECT s.amount, s.frequency, s.status, s.next_date, f.name as fund_name FROM finvox.sips s JOIN finvox.funds f ON s.fund_id = f.id JOIN finvox.portfolios p ON s.portfolio_id = p.id WHERE p.customer_id = '{customer_id}' ORDER BY s.status, s.next_date

Q: What dividends did I receive last year?
SQL: SELECT d.amount, d.record_date, d.payment_date, d.reinvested, f.name as fund_name FROM finvox.dividends d JOIN finvox.funds f ON d.fund_id = f.id JOIN finvox.portfolios p ON d.portfolio_id = p.id WHERE p.customer_id = '{customer_id}' AND d.record_date >= '2025-01-01' ORDER BY d.record_date DESC

Q: How many customers does each RM manage?
SQL: SELECT rm.name, rm.department, COUNT(c.id) as customer_count, rm.aum_managed FROM finvox.relationship_managers rm LEFT JOIN finvox.customers c ON c.relationship_manager_id = rm.id WHERE rm.active = true GROUP BY rm.id, rm.name, rm.department, rm.aum_managed ORDER BY customer_count DESC

Q: What are my open tickets?
SQL: SELECT id, category, subject, priority, status, created_at FROM finvox.tickets WHERE customer_id = '{customer_id}' AND status NOT IN ('resolved', 'closed') ORDER BY created_at DESC

Q: Total AUM across all portfolios
SQL: SELECT SUM(current_value) as total_aum, COUNT(DISTINCT customer_id) as total_clients, COUNT(*) as total_portfolios FROM finvox.portfolios
"""

def _is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper().strip()
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for kw in dangerous:
        if kw in sql_upper.split():
            return False
    return sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")


async def ask_database(pool, question: str, openai_api_key: str, customer_id: str = None) -> str:
    """Convert natural language to SQL, execute, and return voice-friendly answer."""
    client = AsyncOpenAI(api_key=openai_api_key)

    schema = SCHEMA_CONTEXT
    examples = FEW_SHOT_EXAMPLES
    if customer_id:
        examples = examples.replace("{customer_id}", customer_id)

    # Step 1: Generate SQL
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": f"""You are a SQL expert for a financial services company.
Given a question, generate a single PostgreSQL SELECT query.
Always use explicit schema prefix: finvox.table_name
Return ONLY the SQL query, no explanation.

{schema}

Examples:
{examples}"""},
            {"role": "user", "content": question}
        ],
        max_tokens=500,
    )

    sql = resp.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    if not _is_safe_sql(sql):
        return "I can only run read-only queries for security. That request would modify data."

    logger.info(f"NL2SQL: {question} -> {sql}")

    # Step 2: Execute
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql)
            results = [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"SQL error: {e}")
        return f"I had trouble running that query. Could you rephrase your question?"

    if not results:
        return "I didn't find any matching records for that question."

    # Step 3: Summarize to voice-friendly answer
    import json
    # Convert non-serializable types
    for row in results:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
            elif isinstance(v, (type(None),)):
                row[k] = None
            else:
                try:
                    json.dumps(v)
                except (TypeError, ValueError):
                    row[k] = str(v)

    summary_resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": "Summarize this database result into 1-3 concise sentences suitable for a voice response. Use natural language. Include key numbers. Do not mention SQL or databases."},
            {"role": "user", "content": f"Question: {question}\nResults: {json.dumps(results[:20], default=str)}"}
        ],
        max_tokens=200,
    )

    return summary_resp.choices[0].message.content.strip()
