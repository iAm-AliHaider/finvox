"""Fix double OTP: when pre-generated, skip identify_caller and send_verification_otp."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "agent.py"
src = p.read_text(encoding="utf-8")

old = '''            otp_context = f"\\n\\nIMPORTANT: An OTP code has ALREADY been sent to the customer's WhatsApp ({caller_phone}). Tell them you've sent the code and ask them to read it back. When they read it, use verify_caller_otp to verify it."'''

new = '''            otp_context = (
                f"\\n\\nCRITICAL OVERRIDE - OTP ALREADY SENT:"
                f"\\n- The customer is {cust.get('name', 'known')} (ID: {session_state.customer_id})."
                f"\\n- An OTP code has ALREADY been sent to their WhatsApp ({caller_phone})."
                f"\\n- DO NOT call identify_caller (already done)."
                f"\\n- DO NOT call send_verification_otp (already sent)."
                f"\\n- Just greet them by name, tell them you've sent a verification code to their WhatsApp, and ask them to read it back."
                f"\\n- When they read the code, use verify_caller_otp to confirm it."
                f"\\n- After verification, assist with their request."
            )'''

if old not in src:
    print("ERROR: old block not found!")
    raise SystemExit(1)

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("Patched successfully")
