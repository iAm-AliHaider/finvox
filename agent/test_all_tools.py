"""Test all 32 voice tools against the real Neon DB."""
import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from db import database as db

PASS = 0
FAIL = 0
ERRORS = []

async def test(name, coro):
    global PASS, FAIL
    try:
        result = await coro
        if result is None:
            FAIL += 1
            ERRORS.append(f"{name}: returned None")
            print(f"  WARN {name}: returned None")
        else:
            PASS += 1
            preview = str(result)[:120]
            print(f"  OK   {name}: {preview}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"{name}: {e}")
        print(f"  FAIL {name}: {e}")

async def main():
    global PASS, FAIL
    await db.reset_pool()
    pool = await db.get_pool()

    print("\n=== CALLER TOOLS ===")
    # identify_caller
    await test("get_customer_by_phone(known)", db.get_customer_by_phone("+966551234567"))
    await test("get_customer_by_phone(unknown)", db.get_customer_by_phone("+999999999999"))
    # generate + verify OTP
    code = await db.generate_otp("+966551234567", "login")
    print(f"  INFO OTP generated: {code}")
    await test("verify_otp(correct)", db.verify_otp("+966551234567", code))
    await test("verify_otp(wrong)", db.verify_otp("+966551234567", "000000"))
    # create_customer
    # Skip actual creation to avoid polluting DB
    print("  SKIP create_customer (would pollute DB)")

    print("\n=== LOAN TOOLS ===")
    await test("get_customer_loans(C001)", db.get_customer_loans("C001"))
    await test("get_loan_detail(L001)", db.get_loan_detail("L001"))
    await test("get_next_emi(L001)", db.get_next_emi("L001"))
    await test("calculate_prepayment(L001)", db.calculate_prepayment("L001", 50000))
    await test("get_loan_application_status(C001)", db.get_loan_application_status("C001"))
    await test("get_loan_charges(L001)", db.get_loan_charges("L001"))

    print("\n=== INVESTMENT TOOLS ===")
    await test("get_portfolio_summary(C001)", db.get_portfolio_summary("C001"))
    await test("get_portfolio_holdings(C001)", db.get_portfolio_holdings("C001"))
    await test("get_fund_info(F001)", db.get_fund_info("F001"))
    await test("search_funds(equity)", db.search_funds("equity"))
    await test("get_transactions(C001)", db.get_transactions("C001"))
    await test("get_sip_status(C001)", db.get_sip_status("C001"))
    await test("get_dividends(C001)", db.get_dividends("C001"))

    print("\n=== GENERAL TOOLS ===")
    await test("create_support_ticket", db.create_support_ticket("C001", "Test ticket", "testing"))
    await test("get_customer_tickets(C001)", db.get_customer_tickets("C001"))
    await test("schedule_callback", db.schedule_callback("C001", "2026-03-15 10:00", "Follow up"))

    print("\n=== EMPLOYEE TOOLS ===")
    await test("search_customers(faisal)", db.search_customers("faisal"))
    await test("get_delinquency_report", db.get_delinquency_report())
    await test("get_rm_portfolio(RM001)", db.get_rm_portfolio("RM001"))
    await test("get_daily_collections", db.get_daily_collections())
    await test("get_compliance_alerts", db.get_compliance_alerts())

    print("\n=== NL2SQL ===")
    try:
        from text_to_sql import ask_database
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            result = await ask_database(pool, "How many customers do we have?", api_key)
            PASS += 1
            print(f"  OK   ask_database: {str(result)[:120]}")
        else:
            print("  SKIP ask_database (no OPENAI_API_KEY)")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"ask_database: {e}")
        print(f"  FAIL ask_database: {e}")

    print("\n=== WA CLIENT ===")
    try:
        from wa_client import wa_status
        status = await wa_status()
        PASS += 1
        print(f"  OK   wa_status: {status}")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"wa_status: {e}")
        print(f"  FAIL wa_status: {e}")

    print(f"\n{'='*50}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print(f"\nFAILURES:")
        for e in ERRORS:
            print(f"  - {e}")
    print()

asyncio.run(main())

