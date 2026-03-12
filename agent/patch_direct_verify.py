"""Fix: generate_reply doesn't force tool calls - LLM just says 'verified' without calling the tool.
Fix: directly call verify_otp from data channel handler + send otp_verified event.
Also fix: WA summary arriving empty despite summary_len=361 logged."""

with open("agent.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Replace the generate_reply approach with direct verification
old_otp_handler = '''            if msg.get("type") == "otp_submit" and msg.get("code"):
                otp_code = msg["code"]
                logger.info(f"OTP submitted via modal: {otp_code}")
                # Inject into the conversation so the agent processes it
                asyncio.ensure_future(
                    session.generate_reply(
                        instructions=f"The customer just typed their OTP code in the verification modal: {otp_code}. Call verify_caller_otp with this code immediately. Do NOT ask them to read it out loud."
                    )
                )'''

new_otp_handler = '''            if msg.get("type") == "otp_submit" and msg.get("code"):
                otp_code = msg["code"]
                logger.info(f"OTP submitted via modal: {otp_code}")
                # Directly verify - don't rely on LLM to call the tool
                async def _do_verify():
                    try:
                        from db.database import verify_otp, log_audit
                        result = await verify_otp(caller_phone, otp_code, purpose="login")
                        logger.info(f"Direct OTP verify result: {result}")
                        if result["verified"]:
                            await log_audit(None, "MRNA_agent", "otp_verified", "otp", None, {"phone": caller_phone})
                            session_state.verified = True
                            # Send otp_verified event to frontend
                            await room.local_participant.publish_data(
                                json.dumps({"type": "otp_verified", "phone": caller_phone, "timestamp": datetime.utcnow().isoformat()}, default=str).encode(),
                                reliable=True, topic="ui_sync"
                            )
                            logger.info(f"OTP verified and event sent for {caller_phone}")
                            # Tell the agent the customer is verified
                            await session.generate_reply(
                                instructions=f"The customer {session_state.customer_name or 'Ali'} has been verified successfully via OTP. Greet them and ask how you can help."
                            )
                        else:
                            error = result.get("error", "Invalid code")
                            logger.warning(f"OTP verify failed: {error}")
                            await session.generate_reply(
                                instructions=f"The customer entered an incorrect OTP code. Error: {error}. Ask them to try again."
                            )
                    except Exception as e:
                        logger.error(f"Direct OTP verify error: {e}")
                asyncio.ensure_future(_do_verify())'''

if old_otp_handler in code:
    code = code.replace(old_otp_handler, new_otp_handler)
    print("PATCHED: Direct OTP verification (no LLM middleman)")
else:
    print("SKIP: OTP handler not found")

# 2. Fix post-call summary WA - the message might have special chars breaking CLI
# Replace send_call_summary to sanitize the message
old_wa_send = '''        # Send via WA
        from wa_client import send_call_summary
        cust_name = cust.get("name", "Customer") if cust else "Customer"
        logger.info(f"Post-call summary sending: phone={caller_phone}, name={cust_name}, summary_len={len(summary) if summary else 0}, summary={summary[:100] if summary else '(none)'}")
        await send_call_summary(caller_phone, cust_name, summary)
        logger.info(f"Post-call summary sent to {caller_phone}")'''

new_wa_send = '''        # Send via WA - sanitize summary for CLI transport
        from wa_client import send_call_summary
        cust_name = cust.get("name", "Customer") if cust else "Customer"
        # Strip markdown that might break CLI args
        clean_summary = summary.replace("*", "").replace("_", "").replace("`", "") if summary else ""
        logger.info(f"Post-call summary sending: phone={caller_phone}, name={cust_name}, summary_len={len(clean_summary)}, summary={clean_summary[:100]}")
        await send_call_summary(caller_phone, cust_name, clean_summary)
        logger.info(f"Post-call summary sent to {caller_phone}")'''

if old_wa_send in code:
    code = code.replace(old_wa_send, new_wa_send)
    print("PATCHED: Summary sanitized for CLI transport")
else:
    print("SKIP: WA send block not found")

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(code)

print("\nDone! Restart agent.")
