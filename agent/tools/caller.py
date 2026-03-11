"""Caller identification, verification, and new customer onboarding tools."""
import logging
from livekit.agents import function_tool
from db.database import (
    get_customer_by_phone, get_customer, get_customer_loans, get_customer_portfolios,
    verify_otp, generate_otp, log_audit, create_customer
)

logger = logging.getLogger("mrna.tools.caller")

def _notify_ui(event_type: str, data: dict = None):
    """Send event to frontend dashboard."""
    try:
        import sys, os, json, asyncio
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent import _sessions, _send_event
        for room_name, sess in _sessions.items():
            if sess.room:
                _send_event(sess.room, event_type, data or {})
                break
    except Exception as e:
        logger.warning(f"UI notify failed: {e}")


@function_tool(
    name="identify_caller",
    description="Identify a customer by their phone number. Returns customer profile if found, or indicates new caller. ALWAYS use this first at the start of every call."
)
async def identify_caller(phone: str) -> str:
    """Look up customer by phone number."""
    customer = await get_customer_by_phone(phone)
    if not customer:
        return (
            f"No account found for phone {phone}. "
            f"This is a NEW caller. Ask if they would like to create an account with MRNA. "
            f"If yes, collect their full name and use create_new_account to register them. "
            f"You will need to verify their WhatsApp with an OTP before proceeding."
        )

    loans = await get_customer_loans(customer["id"])
    portfolios = await get_customer_portfolios(customer["id"])
    active_loans = [l for l in loans if l.get("status") == "active"]

    result = (
        f"Customer identified: {customer['name']} (ID: {customer['id']}). "
        f"Tier: {customer.get('tier', 'retail')}. KYC: {customer.get('kyc_status', 'valid')}. "
        f"Risk profile: {customer.get('risk_profile', 'moderate')}. "
        f"Active loans: {len(active_loans)}. Portfolios: {len(portfolios)}. "
        f"RM: {customer.get('relationship_manager_id', 'None')}. "
        f"Preferred language: {customer.get('preferred_language', 'en')}."
    )

    if customer.get("kyc_status") == "expired":
        result += " WARNING: KYC is expired. Restrict to read-only operations."

    # Prompt verification
    result += " Now send a verification OTP to confirm their identity before sharing any details."

    await log_audit(customer["id"], "MRNA_agent", "caller_identified",
                    "customer", customer["id"], {"phone": phone})
    return result


@function_tool(
    name="send_verification_otp",
    description="Send a 6-digit OTP to the customer's WhatsApp for identity verification. Use after identifying an EXISTING caller. The OTP will be delivered via WhatsApp."
)
async def send_verification_otp(phone: str) -> str:
    """Generate OTP and send via WhatsApp. Works for both existing and new customers."""
    from wa_client import send_otp, wa_status

    code = await generate_otp(phone, purpose="login")
    status = await wa_status()

    if status == "connected":
        # Look up name if existing customer
        customer = await get_customer_by_phone(phone)
        name = customer["name"] if customer else "Customer"
        sent = await send_otp(phone, code, name)
        if sent:
            delivery = "sent to their WhatsApp"
        else:
            delivery = "generated but WhatsApp delivery failed. Read the code to them"
    else:
        delivery = "generated but WhatsApp is offline. Read the code to them"
        logger.warning(f"WA offline, OTP for {phone}: {code}")

    await log_audit(None, "MRNA_agent", "otp_sent",
                    "otp", None, {"phone": phone, "purpose": "login"})

    _notify_ui("otp_sent", {"phone": phone, "code_length": 6})
    return f"OTP {code} has been {delivery}. Ask the customer to read back the 6-digit code they received."


@function_tool(
    name="verify_caller_otp",
    description="Verify the OTP code the customer reads back. Returns whether verification succeeded. Use for both existing customers and new signups."
)
async def verify_caller_otp(phone: str, code: str) -> str:
    """Verify OTP code."""
    result = await verify_otp(phone, code, purpose="login")
    if result["verified"]:
        await log_audit(None, "MRNA_agent", "otp_verified",
                        "otp", None, {"phone": phone})
        _notify_ui("otp_verified", {"phone": phone})
        return "OTP verified successfully! Identity confirmed. You can now access all account features or proceed with account creation."
    else:
        error = result.get("error", "Verification failed")
        attempts_left = result.get("attempts_left")
        msg = f"Verification failed: {error}."
        if attempts_left is not None:
            msg += f" {attempts_left} attempts remaining."
        msg += " Ask them to check their WhatsApp and try again."
        return msg


@function_tool(
    name="create_new_account",
    description="Create a new customer account after WhatsApp OTP verification. Requires the customer's full name and phone number. Optionally collect email, national ID (Iqama/Saudi ID), and city. ONLY use after OTP is verified."
)
async def create_new_account(
    full_name: str,
    phone: str,
    email: str = "",
    national_id: str = "",
    city: str = ""
) -> str:
    """Create a new customer after OTP verification."""
    # Check if already exists
    existing = await get_customer_by_phone(phone)
    if existing:
        return f"An account already exists for this phone number: {existing['name']} (ID: {existing['id']}). No new account created."

    try:
        customer = await create_customer(
            name=full_name,
            phone=phone,
            email=email or None,
            national_id=national_id or None,
            city=city or None,
        )

        await log_audit(customer["id"], "MRNA_agent", "account_created",
                        "customer", customer["id"], {"phone": phone, "method": "voice_onboarding"})

        _notify_ui("customer_identified", {"customer_id": customer["id"], "phone": phone})

        return (
            f"Account created successfully! "
            f"Customer ID: {customer['id']}. Name: {customer['name']}. "
            f"Tier: Retail. KYC status: Pending. "
            f"Welcome the customer to MRNA and explain that they can now access loan and investment services. "
            f"Let them know their KYC documents will need to be submitted for full account activation."
        )
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        return f"Account creation failed: {str(e)}. Please try again or escalate to a relationship manager."



