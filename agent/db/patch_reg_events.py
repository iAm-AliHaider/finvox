"""Add registration_field events and account_created event to caller tools."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "tools" / "caller.py"
src = p.read_text(encoding="utf-8")

# 1. Update create_new_account to send account_created event
old_notify = '        _notify_ui("customer_identified", {"customer_id": customer["id"], "phone": phone})'
new_notify = '        _notify_ui("account_created", {"customer_id": customer["id"], "phone": phone, "name": customer["name"]})'
src = src.replace(old_notify, new_notify, 1)

# 2. Update the system prompt instruction for new customers in identify_caller
old_new_caller = (
    'f"This is a NEW caller. Ask if they would like to create an account with MRNA. "\n'
    '            f"If yes, collect their full name and use create_new_account to register them. "\n'
    '            f"You will need to verify their WhatsApp with an OTP before proceeding."'
)
new_new_caller = (
    'f"This is a NEW caller. Ask if they would like to create an account with MRNA. "\n'
    '            f"If yes, first send an OTP using send_verification_otp to verify their phone. "\n'
    '            f"After OTP is verified, collect their full name, email, national ID, and city. "\n'
    '            f"Then use create_new_account with all collected details."'
)
src = src.replace(old_new_caller, new_new_caller, 1)

p.write_text(src, encoding="utf-8")
print("Patched caller.py")
