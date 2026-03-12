"""Add WA delivery to statement tool + send_wa_message tool."""
import pathlib

# Patch general.py - add actual WA delivery to request_statement
gen_path = pathlib.Path(__file__).parent.parent / "tools" / "general.py"
gen = gen_path.read_text(encoding="utf-8")

# Add WA delivery after statement request
old_stmt = '''    await log_audit(customer_id, "MRNA_agent", "statement_requested",
                    "statement", None, {"type": statement_type})

    return (
        f"Your {statement_type} statement is being generated. "
        f"It will be sent to your WhatsApp within the next few minutes."
    )'''

new_stmt = '''    await log_audit(customer_id, "MRNA_agent", "statement_requested",
                    "statement", None, {"type": statement_type})

    # Feature 5: Actually send statement notification via WA
    try:
        customer = await get_customer(customer_id)
        if customer and customer.get("phone"):
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from wa_client import send_statement_notification
            await send_statement_notification(
                customer["phone"],
                customer.get("name", "Customer"),
                statement_type
            )
    except Exception as e:
        logger.warning(f"Statement WA notification failed: {e}")

    return (
        f"Your {statement_type} statement has been generated and sent to your WhatsApp. "
        f"Please check your messages."
    )'''

gen = gen.replace(old_stmt, new_stmt, 1)

# Add send_wa_message tool at the end for Feature 3
gen += '''

@function_tool(
    name="send_whatsapp_message",
    description="Send a message to the customer's WhatsApp. Use for sending summaries, confirmations, or follow-up information during the call."
)
async def send_whatsapp_message(customer_id: str, message: str) -> str:
    """Send a WhatsApp message to the customer."""
    customer = await get_customer(customer_id)
    if not customer or not customer.get("phone"):
        return "Cannot send WhatsApp message - customer phone not found."
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from wa_client import send_message
        sent = await send_message(customer["phone"], message)
        if sent:
            await log_audit(customer_id, "MRNA_agent", "wa_message_sent",
                            "communication", None, {"message_preview": message[:50]})
            return "WhatsApp message sent successfully."
        return "Failed to send WhatsApp message. Please try again."
    except Exception as e:
        logger.warning(f"WA message send failed: {e}")
        return f"Failed to send WhatsApp message: {str(e)}"
'''

gen_path.write_text(gen, encoding="utf-8")
print("Patched general.py")

# Now add send_whatsapp_message to agent.py tool imports
agent_path = pathlib.Path(__file__).parent.parent / "agent.py"
agent = agent_path.read_text(encoding="utf-8")

old_import = "from tools.general import (\n    create_support_ticket, get_my_tickets, escalate_to_rm,\n    schedule_callback, update_contact_info, request_statement\n)"
new_import = "from tools.general import (\n    create_support_ticket, get_my_tickets, escalate_to_rm,\n    schedule_callback, update_contact_info, request_statement, send_whatsapp_message\n)"
agent = agent.replace(old_import, new_import, 1)

# Add to CUSTOMER_TOOLS
old_tools = "    create_support_ticket, get_my_tickets, escalate_to_rm,\n    schedule_callback, update_contact_info, request_statement,"
new_tools = "    create_support_ticket, get_my_tickets, escalate_to_rm,\n    schedule_callback, update_contact_info, request_statement, send_whatsapp_message,"
agent = agent.replace(old_tools, new_tools, 1)

agent_path.write_text(agent, encoding="utf-8")
print("Patched agent.py imports")
