"""Investment and portfolio management voice tools."""
import logging
import json
from livekit.agents import function_tool
from db.database import (
    get_customer_portfolios, get_portfolio_detail, get_holdings,
    get_fund_info, search_funds, get_transactions, get_sips,
    get_dividends, get_portfolio_summary, create_ticket, log_audit
)

logger = logging.getLogger("mrna.tools.investments")


@function_tool(
    name="get_portfolio_summary",
    description="Get a high-level summary of all portfolios for a customer including total value, returns, and asset allocation."
)
async def get_portfolio_summary_tool(customer_id: str) -> str:
    summary = await get_portfolio_summary(customer_id)
    if not summary or summary["portfolio_count"] == 0:
        return "This customer has no investment portfolios."

    result = (
        f"Portfolio Summary:\n"
        f"Total invested: SAR {summary['total_invested']:,.0f}\n"
        f"Current value: SAR {summary['current_value']:,.0f}\n"
        f"Total returns: SAR {summary['total_returns']:,.0f} ({summary['returns_pct']}%)\n"
        f"Number of portfolios: {summary['portfolio_count']}\n"
    )

    if summary["allocation"]:
        result += "\nAsset allocation:\n"
        total = summary["current_value"]
        for a in summary["allocation"]:
            val = float(a["total_value"])
            pct = (val / total * 100) if total > 0 else 0
            result += f"  {a['category'].title()}: SAR {val:,.0f} ({pct:.1f}%)\n"

    for p in summary["portfolios"]:
        result += (
            f"\n{p['name']} ({p['type']}): "
            f"SAR {float(p['current_value']):,.0f} ({float(p.get('returns_pct', 0))}% return)"
        )

    return result


@function_tool(
    name="get_portfolio_holdings",
    description="Get detailed fund-wise breakdown of a specific portfolio with current values and P&L."
)
async def get_portfolio_holdings(portfolio_id: str) -> str:
    holdings = await get_holdings(portfolio_id)
    if not holdings:
        return f"No holdings found in portfolio {portfolio_id}."

    lines = [f"Holdings in portfolio {portfolio_id}:"]
    total_value = 0
    total_pnl = 0

    for h in holdings:
        val = float(h.get("current_value", 0))
        pnl = float(h.get("unrealized_pnl", 0))
        total_value += val
        total_pnl += pnl
        pnl_sign = "+" if pnl >= 0 else ""
        lines.append(
            f"  {h['fund_name']} ({h['category']}): "
            f"{float(h['units']):,.2f} units @ SAR {float(h.get('latest_nav', 0)):,.2f} = "
            f"SAR {val:,.0f} ({pnl_sign}SAR {pnl:,.0f})"
        )

    pnl_sign = "+" if total_pnl >= 0 else ""
    lines.append(f"\nTotal: SAR {total_value:,.0f} (P&L: {pnl_sign}SAR {total_pnl:,.0f})")
    return "\n".join(lines)


@function_tool(
    name="get_fund_info",
    description="Get detailed information about a specific investment fund including NAV, returns, risk rating, and expense ratio."
)
async def get_fund_info_tool(fund_id: str) -> str:
    fund = await get_fund_info(fund_id)
    if not fund:
        return f"Fund {fund_id} not found."

    risk_labels = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
    risk = risk_labels.get(fund.get("risk_rating"), "Unknown")

    result = (
        f"{fund['name']} ({fund['category'].title()}):\n"
        f"NAV: SAR {float(fund['nav']):,.2f}\n"
        f"AUM: SAR {float(fund.get('aum', 0)):,.0f}\n"
        f"Risk rating: {risk} ({fund.get('risk_rating')}/5)\n"
        f"Returns: 1M: {fund.get('return_1m')}%, 3M: {fund.get('return_3m')}%, "
        f"1Y: {fund.get('return_1y')}%, 3Y: {fund.get('return_3y')}%\n"
        f"Expense ratio: {fund.get('expense_ratio')}%\n"
        f"Min investment: SAR {float(fund.get('min_investment', 0)):,.0f}"
    )
    return result


@function_tool(
    name="search_funds",
    description="Search for investment funds by name or category (equity, debt, hybrid, sukuk, etc)."
)
async def search_funds_tool(query: str) -> str:
    funds = await search_funds(query)
    if not funds:
        return f"No funds found matching '{query}'."

    lines = [f"Funds matching '{query}':"]
    for f in funds:
        risk_labels = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
        risk = risk_labels.get(f.get("risk_rating"), "?")
        lines.append(
            f"  {f['name']} ({f['category']}): "
            f"NAV SAR {float(f['nav']):,.2f}, 1Y Return: {f.get('return_1y')}%, Risk: {risk}"
        )
    return "\n".join(lines)


@function_tool(
    name="get_transactions",
    description="Get recent transaction history for a portfolio (buys, sells, switches, SIP installments, dividends)."
)
async def get_transactions_tool(portfolio_id: str) -> str:
    txns = await get_transactions(portfolio_id)
    if not txns:
        return f"No transactions found for portfolio {portfolio_id}."

    lines = [f"Recent transactions in portfolio {portfolio_id}:"]
    for t in txns:
        date = str(t.get("executed_at", ""))[:10]
        lines.append(
            f"  {date} - {t['type'].upper()}: {t['fund_name']} - "
            f"{float(t.get('units', 0)):,.2f} units @ SAR {float(t.get('price', 0)):,.2f} = "
            f"SAR {float(t['amount']):,.0f} [{t['status']}]"
        )
    return "\n".join(lines)


@function_tool(
    name="get_sip_status",
    description="Get all SIP (Systematic Investment Plan) details for a portfolio."
)
async def get_sip_status(portfolio_id: str) -> str:
    sips = await get_sips(portfolio_id)
    if not sips:
        return f"No SIPs found for portfolio {portfolio_id}."

    lines = [f"SIPs in portfolio {portfolio_id}:"]
    for s in sips:
        lines.append(
            f"  {s['fund_name']}: SAR {float(s['amount']):,.0f}/{s['frequency']} "
            f"on day {s.get('day_of_month', '?')} - Status: {s['status']} - "
            f"Next: {s.get('next_date', 'N/A')} - "
            f"Total invested: SAR {float(s.get('total_invested', 0)):,.0f} ({s.get('installments_done', 0)} installments)"
        )
    return "\n".join(lines)


@function_tool(
    name="get_dividends",
    description="Get dividend history for a portfolio."
)
async def get_dividends_tool(portfolio_id: str) -> str:
    divs = await get_dividends(portfolio_id)
    if not divs:
        return f"No dividends found for portfolio {portfolio_id}."

    lines = [f"Dividends for portfolio {portfolio_id}:"]
    total = 0
    for d in divs:
        amt = float(d["amount"])
        total += amt
        reinvested = "Reinvested" if d.get("reinvested") else "Paid out"
        lines.append(
            f"  {d.get('record_date', '?')}: {d['fund_name']} - SAR {amt:,.0f} ({reinvested})"
        )
    lines.append(f"\nTotal dividends: SAR {total:,.0f}")
    return "\n".join(lines)


@function_tool(
    name="request_redemption",
    description="Request to sell/redeem units from a fund. Creates a ticket for processing. Requires verbal confirmation from customer."
)
async def request_redemption(customer_id: str, portfolio_id: str, fund_id: str, units: float) -> str:
    fund = await get_fund_info(fund_id)
    fund_name = fund["name"] if fund else fund_id
    estimated_value = units * float(fund["nav"]) if fund else 0

    ticket = await create_ticket(
        customer_id, "investment",
        f"Redemption Request - {fund_name}",
        f"Customer requests redemption of {units} units from {fund_name} in portfolio {portfolio_id}. "
        f"Estimated value: SAR {estimated_value:,.0f} at current NAV.",
        "high"
    )

    await log_audit(customer_id, "MRNA_agent", "redemption_requested",
                    "portfolio", portfolio_id, {
                        "fund_id": fund_id, "units": units,
                        "estimated_value": estimated_value, "ticket_id": ticket["id"]
                    })

    return (
        f"Redemption request created (Ticket {ticket['id']}). "
        f"Selling {units:,.2f} units of {fund_name}, estimated value SAR {estimated_value:,.0f}. "
        f"This will be processed within 2-3 business days. "
        f"Proceeds will be credited to your primary bank account."
    )


@function_tool(
    name="request_fund_switch",
    description="Request to switch investment from one fund to another. Creates a ticket for processing."
)
async def request_fund_switch(customer_id: str, portfolio_id: str,
                               from_fund_id: str, to_fund_id: str, amount: float) -> str:
    from_fund = await get_fund_info(from_fund_id)
    to_fund = await get_fund_info(to_fund_id)
    from_name = from_fund["name"] if from_fund else from_fund_id
    to_name = to_fund["name"] if to_fund else to_fund_id

    ticket = await create_ticket(
        customer_id, "investment",
        f"Fund Switch - {from_name} to {to_name}",
        f"Switch SAR {amount:,.0f} from {from_name} to {to_name} in portfolio {portfolio_id}.",
        "medium"
    )

    await log_audit(customer_id, "MRNA_agent", "switch_requested",
                    "portfolio", portfolio_id, {
                        "from_fund": from_fund_id, "to_fund": to_fund_id,
                        "amount": amount, "ticket_id": ticket["id"]
                    })

    return (
        f"Fund switch request created (Ticket {ticket['id']}). "
        f"Switching SAR {amount:,.0f} from {from_name} to {to_name}. "
        f"This typically takes 2-3 business days. You will receive a confirmation on WhatsApp."
    )


@function_tool(
    name="modify_sip",
    description="Request to modify a SIP - change amount, pause, or stop. Creates a ticket."
)
async def modify_sip(customer_id: str, sip_id: str, action: str, new_amount: float = 0) -> str:
    valid_actions = ["pause", "stop", "increase", "decrease"]
    if action not in valid_actions:
        return f"Invalid action. Choose from: {', '.join(valid_actions)}"

    desc = f"SIP {sip_id}: {action}"
    if action in ("increase", "decrease") and new_amount > 0:
        desc += f" to SAR {new_amount:,.0f}"

    ticket = await create_ticket(
        customer_id, "investment",
        f"SIP Modification - {action.title()}",
        desc, "medium"
    )

    await log_audit(customer_id, "MRNA_agent", "sip_modified",
                    "sip", sip_id, {"action": action, "new_amount": new_amount})

    return (
        f"SIP modification request created (Ticket {ticket['id']}). "
        f"Action: {action.title()} SIP {sip_id}. "
        f"Changes will take effect from the next SIP date."
    )

