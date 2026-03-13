"""UI control tools — lets the agent navigate tabs, show modals, and generate dynamic displays.

The agent sends events via data channel topic "ui_sync".
Frontend listens and renders accordingly.
"""
import json
import logging
import asyncio
from datetime import datetime, timezone
from livekit.agents import function_tool

logger = logging.getLogger("mrna.tools.ui")

# Reference to the current room — set by agent.py entrypoint
_room = None
_session_state = None


def set_room(room, state):
    """Called from agent.py to give UI tools access to the room."""
    global _room, _session_state
    _room = room
    _session_state = state


async def _publish_ui(event_type: str, data: dict = None):
    """Publish a UI event to the frontend via data channel."""
    if not _room:
        logger.warning("No room set for UI publish")
        return
    payload = json.dumps({
        "type": event_type,
        **(data or {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, default=str).encode()
    try:
        await _room.local_participant.publish_data(payload, reliable=True, topic="ui_sync")
        logger.info(f"UI event sent: {event_type}")
    except Exception as e:
        logger.warning(f"UI publish failed ({event_type}): {e}")


# ---- Navigation ----

@function_tool(
    name="navigate_to",
    description="Switch the customer's dashboard to a specific tab. Available tabs: overview, loans, portfolio, transcript, tickets, compliance. Use this when discussing a topic — switch to the relevant tab so the customer can see the data."
)
async def navigate_to(tab: str) -> str:
    valid = ["overview", "loans", "portfolio", "transcript", "tickets", "compliance"]
    if tab not in valid:
        return f"Invalid tab. Available: {', '.join(valid)}"
    await _publish_ui("navigate", {"tab": tab})
    return f"Switched dashboard to {tab} tab."


# ---- Toast notification ----

@function_tool(
    name="show_toast",
    description="Show a brief notification message at the bottom of the screen. Use for confirmations, status updates, or quick info that doesn't need a modal."
)
async def show_toast(message: str) -> str:
    await _publish_ui("toast", {"message": message})
    return "Toast shown."


# ---- Dynamic Modal ----

@function_tool(
    name="show_info_modal",
    description="""Show a rich information modal on the customer's screen. Use when the customer asks about something that needs visual detail — calculations, comparisons, breakdowns, summaries.

Parameters:
- title: Modal title
- subtitle: Optional subtitle
- color: blue, green, red, purple, amber, teal
- size: sm, md, lg, xl
- content_type: One of: loan_detail, portfolio_breakdown, emi_calculator, fund_comparison, payment_schedule, account_summary, custom
- data: JSON object with the relevant data to display

For content_type="custom", provide data with:
- sections: array of section objects
  - {type: "kv", items: [{label, value}]}
  - {type: "table", columns: [{key, label, align, format}], rows: [{...}]}
  - {type: "chart", chart: {type: "bar"|"pie"|"progress", data: [{label, value, color}]}}
  - {type: "summary_box", items: [{label, value}]}
  - {type: "alert", level: "info"|"warning"|"error"|"success", message: "..."}
  - {type: "text", content: "..."}
  - {type: "list", items: [...], ordered: true|false}
  - {type: "divider"}
"""
)
async def show_info_modal(title: str, content_type: str, data: str,
                           subtitle: str = "", color: str = "blue",
                           size: str = "md") -> str:
    try:
        parsed_data = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        return "Invalid JSON in data parameter."

    modal_id = f"modal_{datetime.now().strftime('%H%M%S%f')}"

    # Build modal based on content_type
    if content_type == "custom":
        modal = {
            "id": modal_id,
            "title": title,
            "subtitle": subtitle,
            "color": color,
            "size": size,
            "sections": parsed_data.get("sections", []),
            "actions": parsed_data.get("actions", []),
            "dismissable": True,
        }
    else:
        # Auto-generate sections from structured data
        modal = await _build_modal(modal_id, title, subtitle, color, size, content_type, parsed_data)

    await _publish_ui("show_modal", {"modal": modal})
    return f"Information modal displayed: {title}"


@function_tool(
    name="close_modal",
    description="Close the currently displayed modal on the customer's screen."
)
async def close_modal() -> str:
    await _publish_ui("close_modal", {})
    return "Modal closed."


# ---- Smart modal builders ----

async def _build_modal(modal_id, title, subtitle, color, size, content_type, data):
    """Build structured modal sections based on content_type."""
    sections = []

    if content_type == "loan_detail":
        loan = data
        sections = [
            {"type": "summary_box", "items": [
                {"label": "Principal", "value": f"SAR {_num(loan.get('principal')):,.0f}"},
                {"label": "Outstanding", "value": f"SAR {_num(loan.get('outstanding')):,.0f}"},
                {"label": "Interest Rate", "value": f"{loan.get('interest_rate', 'N/A')}% p.a."},
            ]},
            {"type": "kv", "items": [
                {"label": "Loan ID", "value": str(loan.get("id", ""))},
                {"label": "Type", "value": str(loan.get("type", "")).title()},
                {"label": "Status", "value": str(loan.get("status", "")).title()},
                {"label": "Tenure", "value": f"{loan.get('tenure_months', 'N/A')} months"},
                {"label": "Start Date", "value": str(loan.get("start_date", ""))[:10]},
                {"label": "EMI Amount", "value": f"SAR {_num(loan.get('emi_amount')):,.0f}"},
            ]},
        ]
        if loan.get("payments"):
            sections.append({"type": "table", "columns": [
                {"key": "due_date", "label": "Due Date", "format": "date"},
                {"key": "amount", "label": "Amount", "format": "currency", "align": "right"},
                {"key": "status", "label": "Status", "format": "status", "align": "center"},
            ], "rows": loan["payments"][:6]})

    elif content_type == "portfolio_breakdown":
        port = data
        holdings = port.get("holdings", [])
        sections = [
            {"type": "summary_box", "items": [
                {"label": "Invested", "value": f"SAR {_num(port.get('total_invested')):,.0f}"},
                {"label": "Current Value", "value": f"SAR {_num(port.get('current_value')):,.0f}"},
                {"label": "P&L", "value": f"SAR {_num(port.get('current_value')) - _num(port.get('total_invested')):+,.0f}"},
            ]},
        ]
        if holdings:
            chart_data = []
            for h in holdings:
                val = _num(h.get("units", 0)) * _num(h.get("current_nav", 0))
                chart_data.append({"label": h.get("fund_name", "Unknown"), "value": round(val)})
            sections.append({"type": "chart", "chart": {"type": "pie", "data": chart_data}})
            sections.append({"type": "table", "columns": [
                {"key": "fund_name", "label": "Fund"},
                {"key": "units", "label": "Units", "align": "right"},
                {"key": "current_nav", "label": "NAV", "format": "currency", "align": "right"},
                {"key": "value", "label": "Value", "format": "currency", "align": "right"},
            ], "rows": [
                {**h, "value": round(_num(h.get("units", 0)) * _num(h.get("current_nav", 0)))}
                for h in holdings
            ]})

    elif content_type == "emi_calculator":
        sections = [
            {"type": "summary_box", "items": [
                {"label": "Loan Amount", "value": f"SAR {_num(data.get('principal')):,.0f}"},
                {"label": "Prepayment", "value": f"SAR {_num(data.get('prepayment')):,.0f}"},
                {"label": "New Outstanding", "value": f"SAR {_num(data.get('new_outstanding')):,.0f}"},
            ]},
            {"type": "kv", "items": [
                {"label": "Current EMI", "value": f"SAR {_num(data.get('current_emi')):,.0f}"},
                {"label": "New EMI", "value": f"SAR {_num(data.get('new_emi')):,.0f}"},
                {"label": "Savings/Month", "value": f"SAR {_num(data.get('savings')):,.0f}"},
                {"label": "Interest Saved", "value": f"SAR {_num(data.get('interest_saved')):,.0f}"},
                {"label": "Months Reduced", "value": str(data.get("months_reduced", 0))},
            ]},
            {"type": "alert", "level": "info", "message": data.get("note", "Prepayment is subject to bank approval and applicable charges.")},
        ]

    elif content_type == "fund_comparison":
        funds = data.get("funds", [])
        if funds:
            sections = [
                {"type": "table", "columns": [
                    {"key": "name", "label": "Fund"},
                    {"key": "category", "label": "Category"},
                    {"key": "nav", "label": "NAV", "format": "currency", "align": "right"},
                    {"key": "return_1y", "label": "1Y Return", "format": "percent", "align": "right"},
                    {"key": "risk_rating", "label": "Risk", "align": "center"},
                ], "rows": funds},
                {"type": "chart", "chart": {
                    "type": "bar",
                    "data": [{"label": f.get("name", ""), "value": _num(f.get("return_1y", 0))} for f in funds]
                }},
            ]

    elif content_type == "payment_schedule":
        payments = data.get("payments", [])
        sections = [
            {"type": "summary_box", "items": [
                {"label": "Total Payments", "value": str(len(payments))},
                {"label": "Total Amount", "value": f"SAR {sum(_num(p.get('amount')) for p in payments):,.0f}"},
                {"label": "Paid", "value": str(sum(1 for p in payments if p.get('status') == 'paid'))},
                {"label": "Overdue", "value": str(sum(1 for p in payments if p.get('status') == 'overdue'))},
            ]},
        ]
        if payments:
            sections.append({"type": "table", "columns": [
                {"key": "due_date", "label": "Due Date", "format": "date"},
                {"key": "amount", "label": "Amount", "format": "currency", "align": "right"},
                {"key": "paid_amount", "label": "Paid", "format": "currency", "align": "right"},
                {"key": "late_fee", "label": "Late Fee", "format": "currency", "align": "right"},
                {"key": "status", "label": "Status", "format": "status", "align": "center"},
            ], "rows": payments[:12]})

    elif content_type == "account_summary":
        sections = [
            {"type": "summary_box", "items": [
                {"label": "Total Loans Outstanding", "value": f"SAR {_num(data.get('total_outstanding')):,.0f}"},
                {"label": "Portfolio Value", "value": f"SAR {_num(data.get('portfolio_value')):,.0f}"},
                {"label": "Net Position", "value": f"SAR {_num(data.get('net_position')):,.0f}"},
            ]},
            {"type": "chart", "chart": {
                "type": "pie",
                "data": [
                    {"label": "Investments", "value": round(_num(data.get("portfolio_value"))), "color": "#10b981"},
                    {"label": "Loans", "value": round(_num(data.get("total_outstanding"))), "color": "#ef4444"},
                ]
            }},
        ]
        if data.get("alerts"):
            for alert in data["alerts"]:
                sections.append({"type": "alert", "level": alert.get("level", "info"), "message": alert.get("message", "")})

    return {
        "id": modal_id,
        "title": title,
        "subtitle": subtitle,
        "color": color,
        "size": size,
        "sections": sections,
        "dismissable": True,
    }


def _num(val):
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0
