"""Patch agent.py to add debug logging for WA messages and fix empty summaries."""
import re

with open("agent.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add debug logging to conversation_item_added handler
old_conv = '''    @session.on("conversation_item_added")
    def handle_conv_item(ev):
        item = ev.item
        if hasattr(item, 'role') and item.role == "assistant" and hasattr(item, 'content'):
            text = ""
            if isinstance(item.content, str):
                text = item.content
            elif isinstance(item.content, list):
                text = " ".join(str(c) for c in item.content if c)
            if text:
                masked = mask_pii(text)
                _send_event(room, "transcript", {"role": "agent", "text": masked})
                if caller_phone:
                    add_wa_context(caller_phone, "agent", text)'''

new_conv = '''    @session.on("conversation_item_added")
    def handle_conv_item(ev):
        item = ev.item
        logger.info(f"conversation_item_added: type={type(item).__name__}, attrs={[a for a in dir(item) if not a.startswith('_')]}")
        text = ""
        # Try multiple attribute paths for agent text
        if hasattr(item, 'role') and item.role == "assistant":
            if hasattr(item, 'content'):
                if isinstance(item.content, str):
                    text = item.content
                elif isinstance(item.content, list):
                    text = " ".join(str(c) for c in item.content if c)
            if not text and hasattr(item, 'text_content'):
                text = str(item.text_content) if item.text_content else ""
            if not text and hasattr(item, 'output'):
                text = str(item.output) if item.output else ""
            logger.info(f"conversation_item_added assistant text={text[:100] if text else '(empty)'}")
        if text:
            masked = mask_pii(text)
            _send_event(room, "transcript", {"role": "agent", "text": masked})
            if caller_phone:
                add_wa_context(caller_phone, "agent", text)'''

if old_conv in code:
    code = code.replace(old_conv, new_conv)
    print("PATCHED: conversation_item_added handler with debug logging")
else:
    print("SKIP: conversation_item_added handler not found (maybe already patched)")

# 2. Fix _send_post_call_summary to not silently return on empty context
old_summary = '''    async def _send_post_call_summary():
        """Generate and send call summary via WhatsApp after disconnect."""
        if not caller_phone:
            return
        wa_sess = get_wa_session(caller_phone)
        if not wa_sess or not wa_sess["context"]:
            return'''

new_summary = '''    async def _send_post_call_summary():
        """Generate and send call summary via WhatsApp after disconnect."""
        if not caller_phone:
            logger.info("Post-call summary: no caller_phone, skipping")
            return
        wa_sess = get_wa_session(caller_phone)
        logger.info(f"Post-call summary: wa_sess exists={wa_sess is not None}, context_len={len(wa_sess['context']) if wa_sess and wa_sess.get('context') else 0}")
        if not wa_sess or not wa_sess.get("context"):
            # Still send a basic summary even without transcript context
            logger.info("Post-call summary: no context, sending basic summary")
            from wa_client import send_call_summary
            cust_name = cust.get("name", "Customer") if cust else "Customer"
            await send_call_summary(caller_phone, cust_name, "Thank you for calling MRNA Financial Services. If you need further assistance, please call us again or reply to this message.")
            return'''

if old_summary in code:
    code = code.replace(old_summary, new_summary)
    print("PATCHED: _send_post_call_summary with fallback for empty context")
else:
    print("SKIP: _send_post_call_summary not found")

# 3. Add logging before send_call_summary
old_send = '''        # Send via WA
        from wa_client import send_call_summary
        cust_name = cust.get("name", "Customer") if cust else "Customer"
        await send_call_summary(caller_phone, cust_name, summary)
        logger.info(f"Post-call summary sent to {caller_phone}")'''

new_send = '''        # Send via WA
        from wa_client import send_call_summary
        cust_name = cust.get("name", "Customer") if cust else "Customer"
        logger.info(f"Post-call summary sending: phone={caller_phone}, name={cust_name}, summary_len={len(summary) if summary else 0}, summary={summary[:100] if summary else '(none)'}")
        await send_call_summary(caller_phone, cust_name, summary)
        logger.info(f"Post-call summary sent to {caller_phone}")'''

if old_send in code:
    code = code.replace(old_send, new_send)
    print("PATCHED: send_call_summary with debug logging")
else:
    print("SKIP: send_call_summary logging not found")

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Done! Restart agent to apply.")
