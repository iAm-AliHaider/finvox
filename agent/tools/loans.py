"""Loan management voice tools."""
import logging
from livekit.agents import function_tool
from db.database import (
    get_customer_loans, get_loan_detail, get_payment_history,
    get_next_emi, calculate_prepayment, get_loan_applications,
    get_overdue_summary, create_ticket, log_audit
)

logger = logging.getLogger("mrna.tools.loans")


@function_tool(
    name="get_loans",
    description="Get all loans for a customer. Shows type, outstanding balance, EMI, status, and overdue count."
)
async def get_loans(customer_id: str) -> str:
    loans = await get_customer_loans(customer_id)
    if not loans:
        return "This customer has no loans."

    lines = []
    for l in loans:
        overdue = l.get("overdue_count", 0)
        line = (
            f"{l['type'].title()} loan {l['id']}: "
            f"Outstanding SAR {float(l['outstanding']):,.0f}, "
            f"EMI SAR {float(l['emi_amount']):,.0f}/month, "
            f"Rate {float(l['interest_rate'])}%, "
            f"Status: {l['status']}"
        )
        if overdue > 0:
            line += f" - {overdue} OVERDUE payments"
        lines.append(line)

    return "Customer loans:\n" + "\n".join(lines)


@function_tool(
    name="get_loan_detail",
    description="Get detailed information about a specific loan including recent payment history."
)
async def get_loan_detail_tool(loan_id: str) -> str:
    data = await get_loan_detail(loan_id)
    if not data:
        return f"Loan {loan_id} not found."

    loan = data["loan"]
    payments = data["payments"]

    result = (
        f"Loan {loan['id']} ({loan['type'].title()}):\n"
        f"Principal: SAR {float(loan['principal']):,.0f}\n"
        f"Outstanding: SAR {float(loan['outstanding']):,.0f}\n"
        f"Interest rate: {float(loan['interest_rate'])}%\n"
        f"EMI: SAR {float(loan['emi_amount']):,.0f}/month\n"
        f"Tenure: {loan['tenure_months']} months\n"
        f"Start: {loan['start_date']}, Maturity: {loan['maturity_date']}\n"
        f"Status: {loan['status']}\n"
    )

    if loan.get("collateral"):
        result += f"Collateral: {loan['collateral']}\n"

    if payments:
        result += "\nRecent payments:\n"
        for p in payments[:6]:
            late = f" (Late fee: SAR {float(p['late_fee'])})" if float(p.get('late_fee', 0)) > 0 else ""
            result += f"  {p['due_date']}: SAR {float(p['amount_due']):,.0f} - {p['status']}{late}\n"

    return result


@function_tool(
    name="get_next_emi",
    description="Get the next upcoming EMI payment details for a loan."
)
async def get_next_emi_tool(loan_id: str) -> str:
    payment = await get_next_emi(loan_id)
    if not payment:
        return f"No upcoming EMI found for loan {loan_id}. All payments may be current."

    late_fee = float(payment.get("late_fee", 0))
    total = float(payment["amount_due"]) + late_fee

    result = (
        f"Next EMI for loan {loan_id}:\n"
        f"Due date: {payment['due_date']}\n"
        f"Amount: SAR {float(payment['amount_due']):,.0f}\n"
        f"Status: {payment['status']}"
    )
    if late_fee > 0:
        result += f"\nLate fee: SAR {late_fee:,.0f}\nTotal due: SAR {total:,.0f}"
    return result


@function_tool(
    name="calculate_prepayment",
    description="Calculate prepayment details for a loan - new balance and estimated interest savings."
)
async def calculate_prepayment_tool(loan_id: str, amount: float) -> str:
    result = await calculate_prepayment(loan_id, amount)
    if "error" in result:
        return result["error"]

    return (
        f"Prepayment calculation for loan {loan_id}:\n"
        f"Current outstanding: SAR {result['current_outstanding']:,.0f}\n"
        f"Prepayment amount: SAR {result['prepayment_amount']:,.0f}\n"
        f"New outstanding: SAR {result['new_outstanding']:,.0f}\n"
        f"Estimated interest saved: SAR {result['estimated_interest_saved']:,.0f}\n"
        f"Prepayment penalty: SAR {result['prepayment_penalty']:,.0f}"
    )


@function_tool(
    name="get_loan_application_status",
    description="Check the status of pending loan applications for a customer."
)
async def get_loan_application_status(customer_id: str) -> str:
    apps = await get_loan_applications(customer_id)
    if not apps:
        return "No loan applications found for this customer."

    lines = []
    for a in apps:
        line = (
            f"Application {a['id']}: {a['type'].title()} loan for SAR {float(a['amount_requested']):,.0f} - "
            f"Status: {a['status'].replace('_', ' ').title()}"
        )
        if a.get("notes"):
            line += f" ({a['notes']})"
        lines.append(line)

    return "Loan applications:\n" + "\n".join(lines)


@function_tool(
    name="explain_charges",
    description="Explain fees, late charges, and interest breakdown for a specific loan."
)
async def explain_charges(loan_id: str) -> str:
    data = await get_loan_detail(loan_id)
    if not data:
        return f"Loan {loan_id} not found."

    loan = data["loan"]
    payments = data["payments"]

    total_late_fees = sum(float(p.get("late_fee", 0)) for p in payments)
    overdue_payments = [p for p in payments if p["status"] == "overdue"]
    partial_payments = [p for p in payments if p["status"] == "partial"]

    result = (
        f"Charge breakdown for loan {loan['id']}:\n"
        f"Interest rate: {float(loan['interest_rate'])}% per annum\n"
        f"Monthly EMI: SAR {float(loan['emi_amount']):,.0f}\n"
        f"Total late fees accumulated: SAR {total_late_fees:,.0f}\n"
        f"Overdue payments: {len(overdue_payments)}\n"
        f"Partial payments: {len(partial_payments)}\n"
    )

    if overdue_payments:
        total_overdue = sum(float(p["amount_due"]) - float(p.get("amount_paid", 0)) for p in overdue_payments)
        result += f"Total overdue amount: SAR {total_overdue:,.0f}\n"

    result += "\nLate fee policy: SAR 150-500 per missed payment depending on loan type."
    return result


@function_tool(
    name="request_emi_reschedule",
    description="Create a request to reschedule EMI payments. This creates a ticket for the relationship manager to process."
)
async def request_emi_reschedule(customer_id: str, loan_id: str, reason: str) -> str:
    ticket = await create_ticket(
        customer_id, "loan",
        f"EMI Reschedule Request - Loan {loan_id}",
        f"Customer requests EMI reschedule for loan {loan_id}. Reason: {reason}",
        "medium"
    )
    await log_audit(customer_id, "MRNA_agent", "emi_reschedule_requested",
                    "loan", loan_id, {"reason": reason, "ticket_id": ticket["id"]})
    return (
        f"EMI reschedule request created (Ticket {ticket['id']}). "
        f"Your relationship manager will review and contact you within 2 business days. "
        f"Please note that reschedules may incur additional interest."
    )

