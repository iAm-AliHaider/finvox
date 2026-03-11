"""Runtime test: call each @function_tool directly as the LLM would."""
import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

PASS = 0
FAIL = 0
ERRORS = []

async def test(name, coro):
    global PASS, FAIL
    try:
        result = await coro
        PASS += 1
        preview = str(result)[:150].replace("\n"," ")
        print(f"  OK   {name}: {preview}")
    except Exception as e:
        FAIL += 1
        err = f"{type(e).__name__}: {e}"
        ERRORS.append(f"{name}: {err}")
        print(f"  FAIL {name}: {err}")

async def main():
    from db.database import reset_pool
    await reset_pool()

    # Import all tools
    from tools.caller import identify_caller, send_verification_otp, verify_caller_otp, create_new_account
    from tools.loans import (get_loans, get_loan_detail_tool, get_next_emi_tool,
        calculate_prepayment_tool, get_loan_application_status, explain_charges, request_emi_reschedule)
    from tools.investments import (get_portfolio_summary_tool, get_portfolio_holdings, get_fund_info_tool,
        search_funds_tool, get_transactions_tool, get_sip_status, get_dividends_tool,
        request_redemption, request_fund_switch, modify_sip)
    from tools.general import (create_support_ticket, get_my_tickets, escalate_to_rm,
        schedule_callback, update_contact_info, request_statement)
    from tools.employee import (search_customer_tool, get_delinquency_report,
        get_rm_portfolio_summary, get_daily_collections_tool, get_compliance_alerts)

    # Each tool._func is the actual async function
    print("\n=== CALLER (4 tools) ===")
    await test("identify_caller", identify_caller._func(phone="+966551234567"))
    await test("identify_caller(unknown)", identify_caller._func(phone="+999999999"))
    await test("send_verification_otp", send_verification_otp._func(phone="+966551234567"))
    await test("verify_caller_otp(wrong)", verify_caller_otp._func(phone="+966551234567", code="000000"))
    # skip create_new_account

    print("\n=== LOANS (7 tools) ===")
    await test("get_loans", get_loans._func(customer_id="C001"))
    await test("get_loan_detail", get_loan_detail_tool._func(loan_id="L001"))
    await test("get_next_emi", get_next_emi_tool._func(loan_id="L001"))
    await test("calculate_prepayment", calculate_prepayment_tool._func(loan_id="L001", amount=50000))
    await test("get_loan_application_status", get_loan_application_status._func(customer_id="C001"))
    await test("explain_charges", explain_charges._func(loan_id="L001"))
    await test("request_emi_reschedule", request_emi_reschedule._func(customer_id="C001", loan_id="L001", reason="Financial hardship"))

    print("\n=== INVESTMENTS (10 tools) ===")
    await test("get_portfolio_summary", get_portfolio_summary_tool._func(customer_id="C001"))
    await test("get_portfolio_holdings", get_portfolio_holdings._func(portfolio_id="P001"))
    await test("get_fund_info", get_fund_info_tool._func(fund_id="F001"))
    await test("search_funds", search_funds_tool._func(query="equity"))
    await test("get_transactions", get_transactions_tool._func(portfolio_id="P001"))
    await test("get_sip_status", get_sip_status._func(portfolio_id="P001"))
    await test("get_dividends", get_dividends_tool._func(portfolio_id="P001"))
    await test("request_redemption", request_redemption._func(customer_id="C001", portfolio_id="P001", fund_id="F001", units=10))
    await test("request_fund_switch", request_fund_switch._func(customer_id="C001", portfolio_id="P001", from_fund_id="F001", to_fund_id="F002", amount=50000))
    await test("modify_sip", modify_sip._func(customer_id="C001", sip_id="SIP001", new_amount=6000, action="increase"))

    print("\n=== GENERAL (6 tools) ===")
    await test("create_support_ticket", create_support_ticket._func(customer_id="C001", category="general", subject="Test", description="Automated test"))
    await test("get_my_tickets", get_my_tickets._func(customer_id="C001"))
    await test("escalate_to_rm", escalate_to_rm._func(customer_id="C001", reason="Testing escalation"))
    await test("schedule_callback", schedule_callback._func(customer_id="C001", preferred_time="2026-03-15 10:00", topic="Follow up"))
    await test("update_contact_info", update_contact_info._func(customer_id="C001", field="city", new_value="Jeddah"))
    await test("request_statement", request_statement._func(customer_id="C001", statement_type="loan"))

    print("\n=== EMPLOYEE (5 tools) ===")
    await test("search_customer", search_customer_tool._func(query="faisal"))
    await test("get_delinquency_report", get_delinquency_report._func())
    await test("get_rm_portfolio_summary", get_rm_portfolio_summary._func(rm_id="RM001"))
    await test("get_daily_collections", get_daily_collections_tool._func())
    await test("get_compliance_alerts", get_compliance_alerts._func())

    print(f"\n{'='*60}")
    print(f"TOTAL: {PASS} passed, {FAIL} failed out of {PASS+FAIL}")
    if ERRORS:
        print(f"\nFAILURES:")
        for e in ERRORS:
            print(f"  - {e}")

asyncio.run(main())





