"""General support tools - tickets, escalation, statements, callbacks."""
import logging
from livekit.agents import function_tool
from db.database import (
    create_ticket, get_customer_tickets, update_customer_field,
    create_notification, log_audit, search_customer, get_customer
)

logger = logging.getLogger("finvox.tools.general")


@function_tool(
    name="create_support_ticket",
    description="Create a support ticket for the customer. Categories: general, loan, investment, account, complaint, kyc, technical. Priorities: low, medium, high, urgent."
)
async def create_support_ticket(customer_id: str, category: str, subject: str,
                                 description: str = "", priority: str = "medium") -> str:
    ticket = await create_ticket(customer_id, category, subject, description, priority)
    await log_audit(customer_id, "finvox_agent", "ticket_created",
                    "ticket", ticket["id"], {"category": category, "priority": priority})
    return (
        f"Support ticket {ticket['id']} created successfully. "
        f"Category: {category}, Priority: {priority}. "
        f"Your relationship manager will follow up within 24 hours."
    )


@function_tool(
    name="get_my_tickets",
    description="Get all support tickets for the current customer."
)
async def get_my_tickets(customer_id: str) -> str:
    tickets = await get_customer_tickets(customer_id)
    if not tickets:
        return "You have no support tickets."

    open_tickets = [t for t in tickets if t["status"] not in ("resolved", "closed")]
    closed_tickets = [t for t in tickets if t["status"] in ("resolved", "closed")]

    lines = []
    if open_tickets:
        lines.append(f"Open tickets ({len(open_tickets)}):")
        for t in open_tickets:
            lines.append(f"  {t['id']}: {t['subject']} [{t['priority']}] - {t['status']}")
    if closed_tickets:
        lines.append(f"\nResolved tickets ({len(closed_tickets)}):")
        for t in closed_tickets[:5]:
            lines.append(f"  {t['id']}: {t['subject']} - {t['status']}")

    return "\n".join(lines)


@function_tool(
    name="escalate_to_rm",
    description="Escalate the call to the customer's relationship manager. Creates an urgent ticket and flags for callback."
)
async def escalate_to_rm(customer_id: str, reason: str) -> str:
    customer = await get_customer(customer_id)
    rm_id = customer.get("relationship_manager_id") if customer else None

    ticket = await create_ticket(
        customer_id, "general",
        f"Escalation: {reason}",
        f"Customer requested escalation to relationship manager. Reason: {reason}",
        "urgent"
    )

    await log_audit(customer_id, "finvox_agent", "escalated_to_rm",
                    "ticket", ticket["id"], {"rm_id": rm_id, "reason": reason})

    if rm_id:
        await create_notification(
            customer_id,
            f"Your request has been escalated to your relationship manager (Ref: {ticket['id']}). They will contact you shortly.",
            "whatsapp", "alert"
        )

    return (
        f"I have escalated your request (Ticket {ticket['id']}). "
        f"Your relationship manager will contact you within the next 2 hours. "
        f"Is there anything else I can help with in the meantime?"
    )


@function_tool(
    name="schedule_callback",
    description="Schedule a callback from the relationship manager at a specific time."
)
async def schedule_callback(customer_id: str, preferred_time: str, topic: str) -> str:
    ticket = await create_ticket(
        customer_id, "general",
        f"Callback Request: {topic}",
        f"Customer requests callback at {preferred_time}. Topic: {topic}",
        "medium"
    )

    await create_notification(
        customer_id,
        f"Callback scheduled for {preferred_time} regarding {topic}. Reference: {ticket['id']}",
        "whatsapp", "reminder"
    )

    await log_audit(customer_id, "finvox_agent", "callback_scheduled",
                    "ticket", ticket["id"], {"preferred_time": preferred_time, "topic": topic})

    return (
        f"Callback scheduled (Ref: {ticket['id']}). "
        f"Your relationship manager will call you at {preferred_time} to discuss {topic}. "
        f"A confirmation has been sent to your WhatsApp."
    )


@function_tool(
    name="update_contact_info",
    description="Update customer contact information (phone, email, address, city). Requires verified session."
)
async def update_contact_info(customer_id: str, field: str, new_value: str) -> str:
    allowed = {"phone", "email", "address", "city"}
    if field not in allowed:
        return f"Cannot update {field}. Allowed fields: {', '.join(allowed)}."

    success = await update_customer_field(customer_id, field, new_value)
    if not success:
        return "Update failed. Please try again or contact support."

    await log_audit(customer_id, "finvox_agent", "contact_updated",
                    "customer", customer_id, {"field": field, "new_value": new_value})

    await create_notification(
        customer_id,
        f"Your {field} has been updated to: {new_value}. If you did not make this change, contact us immediately.",
        "whatsapp", "alert"
    )

    return (
        f"Your {field} has been updated to {new_value}. "
        f"A confirmation has been sent to your WhatsApp."
    )


@function_tool(
    name="request_statement",
    description="Request an account, portfolio, loan, or tax statement. It will be sent via WhatsApp."
)
async def request_statement(customer_id: str, statement_type: str) -> str:
    valid_types = ["account", "portfolio", "loan", "tax", "transaction"]
    if statement_type not in valid_types:
        return f"Invalid type. Available: {', '.join(valid_types)}."

    await create_notification(
        customer_id,
        f"Your {statement_type} statement is being generated. It will be sent to your WhatsApp shortly.",
        "whatsapp", "info"
    )

    await log_audit(customer_id, "finvox_agent", "statement_requested",
                    "statement", None, {"type": statement_type})

    return (
        f"Your {statement_type} statement is being generated. "
        f"It will be sent to your WhatsApp within the next few minutes."
    )
