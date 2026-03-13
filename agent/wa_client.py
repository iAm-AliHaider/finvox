"""WhatsApp client — Browser automation (primary) + Gateway API (fallback).

Browser server on port 8098 uses real WhatsApp Web via Playwright.
Gateway API on port 18789 uses Baileys (may fail for some numbers).
"""
import logging
import json
import urllib.request

logger = logging.getLogger("mrna.wa")

BROWSER_URL = "http://127.0.0.1:8098/send"
GATEWAY_URL = "http://127.0.0.1:18789/tools/invoke"
GATEWAY_TOKEN = "e91afda12f567eeeacf34ab8199adb60edbdc8d6d6038f53"


def _send_via_browser(phone: str, message: str) -> bool:
    """Send via Playwright WhatsApp Web automation."""
    payload = json.dumps({"phone": phone, "message": message}).encode()
    req = urllib.request.Request(
        BROWSER_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = json.loads(resp.read().decode())
        if body.get("ok"):
            logger.info(f"WA browser sent to {phone} OK (len={len(message)})")
            return True
        logger.warning(f"WA browser returned ok=false: {body}")
        return False
    except Exception as e:
        logger.warning(f"WA browser send failed: {e}")
        return False


def _send_via_gateway(phone: str, message: str) -> bool:
    """Send via OpenClaw Gateway HTTP API (Baileys)."""
    payload = json.dumps({
        "tool": "message",
        "args": {
            "action": "send",
            "target": phone,
            "message": message,
            "channel": "whatsapp",
        },
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATEWAY_TOKEN}",
    }
    req = urllib.request.Request(GATEWAY_URL, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        body = json.loads(resp.read().decode())
        if body.get("ok"):
            logger.info(f"WA gateway sent to {phone} OK (len={len(message)})")
            return True
        logger.warning(f"WA gateway returned ok=false: {body}")
        return False
    except Exception as e:
        logger.warning(f"WA gateway send failed: {e}")
        return False


def _send_sync(phone: str, message: str) -> bool:
    """Send WhatsApp message — browser first, gateway fallback."""
    # Try browser automation first
    if _send_via_browser(phone, message):
        return True
    # Fall back to gateway API
    logger.info(f"Browser failed, trying gateway for {phone}")
    return _send_via_gateway(phone, message)


def _send_file_sync(phone: str, file_path: str, caption: str = "") -> bool:
    """Send a file via Gateway HTTP API (browser doesn't support files yet)."""
    args = {
        "action": "send",
        "target": phone,
        "filePath": file_path,
        "channel": "whatsapp",
    }
    if caption:
        args["caption"] = caption
    payload = json.dumps({"tool": "message", "args": args}).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATEWAY_TOKEN}",
    }
    req = urllib.request.Request(GATEWAY_URL, data=payload, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = json.loads(resp.read().decode())
        if body.get("ok"):
            logger.info(f"WA file sent to {phone} OK (path={file_path})")
            return True
        logger.warning(f"WA file send failed: {body}")
        return False
    except Exception as e:
        logger.warning(f"WA file send error: {e}")
        return False


async def _send(phone: str, message: str) -> bool:
    """Async wrapper."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_sync, phone, message)


async def _send_file(phone: str, file_path: str, caption: str = "") -> bool:
    """Async wrapper for file sending."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_file_sync, phone, file_path, caption)


async def send_otp(phone: str, code: str, customer_name: str = "") -> bool:
    message = f"MRNA Security Code: {code} (valid 5 minutes). Do not share this code with anyone."
    return await _send(phone, message)


async def send_call_summary(phone: str, customer_name: str, summary: str) -> bool:
    message = (
        f"*Call Summary - MRNA*\n\n"
        f"Hello {customer_name},\n\n"
        f"{summary}\n\n"
        f"For queries, reply to this message or call us.\n"
        f"_MRNA Financial Services_"
    )
    return await _send(phone, message)


async def send_statement(phone: str, customer_name: str, statement_type: str,
                          text_summary: str, pdf_path: str = "") -> bool:
    """Send statement: text summary first, then PDF attachment if available."""
    text_ok = await _send(phone, text_summary)
    pdf_ok = True
    if pdf_path:
        import os
        if os.path.exists(pdf_path):
            caption = f"MRNA {statement_type.title()} Statement - {customer_name}"
            pdf_ok = await _send_file(phone, pdf_path, caption)
        else:
            logger.warning(f"PDF path does not exist: {pdf_path}")
            pdf_ok = False
    return text_ok and pdf_ok


async def send_message(phone: str, message: str) -> bool:
    return await _send(phone, message)


async def wa_status() -> str:
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:8098/status", timeout=3)
        data = json.loads(resp.read().decode())
        return "connected" if data.get("ready") else "not_logged_in"
    except Exception:
        return "browser_offline"
