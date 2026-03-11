"""Employee/internal tools - elevated access for staff and RMs."""
import logging
from livekit.agents import function_tool
from db.database import (
    search_customer, get_overdue_summary, get_rm_portfolio,
    get_daily_collections, get_compliance_flags, log_audit
)

logger = logging.getLogger("finvox.tools.employee")


@function_tool(
    name="search_customer",
    description="[EMPLOYEE] Search for any customer by name, phone, email, or national ID."
)
async def search_customer_tool(query: str) -> str:
    results = await search_customer(query)
    if not results:
        return f"No customers found matching '{query}'."

    lines = [f"Found {len(results)} customer(s):"]
    for c in results:
        lines.append(
            f"  {c['id']}: {c['name']} | {c['phone']} | {c.get('email', 'N/A')} | "
            f"Tier: {c['tier']} | KYC: {c['kyc_status']}"
        )
    return "\n".join(lines)


@function_tool(
    name="get_delinquency_report",
    description="[EMPLOYEE] Get all overdue loan payments across all customers or for a specific customer."
)
async def get_delinquency_report(customer_id: str = "") -> str:
    overdue = await get_overdue_summary(customer_id if customer_id else None)
    if not overdue:
        return "No overdue payments found."

    total_overdue = sum(float(o["amount_due"]) - float(o.get("amount_paid", 0)) for o in overdue)

    lines = [f"Delinquency Report ({len(overdue)} overdue payments, Total: SAR {total_overdue:,.0f}):"]
    for o in overdue:
        amount_owed = float(o["amount_due"]) - float(o.get("amount_paid", 0))
        lines.append(
            f"  {o.get('customer_name', '?')} | {o.get('loan_type', '?')} loan | "
            f"Due: {o['due_date']} | Owed: SAR {amount_owed:,.0f} | "
            f"Late fee: SAR {float(o.get('late_fee', 0)):,.0f}"
        )
    return "\n".join(lines)


@function_tool(
    name="get_rm_portfolio_summary",
    description="[EMPLOYEE] Get a relationship manager's client portfolio - all assigned customers with AUM and loan counts."
)
async def get_rm_portfolio_summary(rm_id: str) -> str:
    data = await get_rm_portfolio(rm_id)
    if not data:
        return f"Relationship manager {rm_id} not found."

    rm = data["rm"]
    customers = data["customers"]

    lines = [
        f"RM: {rm['name']} ({rm['department'].title()})",
        f"Total clients: {len(customers)} | AUM: SAR {float(rm.get('aum_managed', 0)):,.0f}",
        "",
        "Clients:"
    ]

    for c in customers:
        aum = float(c.get("total_aum", 0) or 0)
        lines.append(
            f"  {c['name']} ({c['tier']}) | {c.get('active_loans', 0)} loans | "
            f"AUM: SAR {aum:,.0f}"
        )

    return "\n".join(lines)


@function_tool(
    name="get_daily_collections",
    description="[EMPLOYEE] Get today's loan payment collections summary."
)
async def get_daily_collections_tool() -> str:
    data = await get_daily_collections()

    result = (
        f"Daily Collections Report ({data['date']}):\n"
        f"Payments due: {data['payments_due']}\n"
        f"Total due: SAR {data['total_due']:,.0f}\n"
        f"Total collected: SAR {data['total_collected']:,.0f}\n"
        f"Collection rate: {data['collection_rate']}%"
    )

    if data["details"]:
        result += "\n\nDetails:"
        for d in data["details"]:
            status_icon = "PAID" if d["status"] == "paid" else "PENDING"
            result += f"\n  {d.get('customer_name', '?')}: SAR {float(d['amount_due']):,.0f} [{status_icon}]"

    return result


@function_tool(
    name="get_compliance_alerts",
    description="[EMPLOYEE] Get all open compliance flags - KYC expiry, AML alerts, overdue payments, etc."
)
async def get_compliance_alerts(customer_id: str = "") -> str:
    flags = await get_compliance_flags(customer_id if customer_id else None)
    if not flags:
        return "No open compliance flags."

    lines = [f"Compliance Alerts ({len(flags)} open):"]
    for f in flags:
        lines.append(
            f"  [{f['severity'].upper()}] {f['type'].replace('_', ' ').title()} - "
            f"{f.get('customer_name', '?')} | {f.get('details', '')[:80]} | Status: {f['status']}"
        )
    return "\n".join(lines)
