"""WhatsApp companion client — sends OTPs, summaries, statements."""
import os
import logging
import aiohttp

logger = logging.getLogger("finvox.wa")
WA_URL = os.environ.get("WA_COMPANION_URL", "http://localhost:8087")


async def send_otp(phone: str, code: str, customer_name: str = "") -> bool:
    """Send OTP to customer WhatsApp."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WA_URL}/otp",
                json={"phone": phone, "code": code, "customer_name": customer_name},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                data = await resp.json()
                return data.get("success", False)
    except Exception as e:
        logger.warning(f"WA OTP send failed: {e}")
        return False


async def send_call_summary(phone: str, customer_name: str, summary: str) -> bool:
    """Send post-call summary to customer WhatsApp."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WA_URL}/summary",
                json={"phone": phone, "customer_name": customer_name, "summary": summary},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                data = await resp.json()
                return data.get("success", False)
    except Exception as e:
        logger.warning(f"WA summary send failed: {e}")
        return False


async def send_statement_notification(phone: str, customer_name: str, statement_type: str) -> bool:
    """Notify customer their statement is ready via WhatsApp."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WA_URL}/statement",
                json={"phone": phone, "customer_name": customer_name, "statement_type": statement_type},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                data = await resp.json()
                return data.get("success", False)
    except Exception as e:
        logger.warning(f"WA statement notify failed: {e}")
        return False


async def send_message(phone: str, message: str) -> bool:
    """Send arbitrary message via WhatsApp."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WA_URL}/send",
                json={"phone": phone, "message": message},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                data = await resp.json()
                return data.get("success", False)
    except Exception as e:
        logger.warning(f"WA send failed: {e}")
        return False


async def wa_status() -> str:
    """Get WhatsApp connection status."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{WA_URL}/health",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as resp:
                data = await resp.json()
                return data.get("status", "unknown")
    except Exception:
        return "offline"
