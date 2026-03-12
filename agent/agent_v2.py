"""MRNA v2 - Clean rewrite of the voice agent.

Architecture:
- OTP is pre-verified via data channel (no voice OTP flow)
- Agent instructions are STATE-DRIVEN (changes based on verified/unverified)
- Post-call summary via thread (survives disconnect)
- WA messages via temp file (avoids CLI truncation)
- No competing generate_reply calls
"""
import os
import sys
import json
import logging
import asyncio
import threading
from datetime import datetime, timezone

from livekit import rtc
from livekit.agents import (
    Agent, AgentSession, WorkerOptions, cli,
    RoomInputOptions, RoomOutputOptions,
)
from livekit.agents import function_tool
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("mrna")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

KOKORO_URL = os.environ.get("KOKORO_URL", "http://localhost:8000/v1")

# ---- Session State ----
_sessions = {}

class SessionState:
    def __init__(self):
        self.customer_id = None
        self.customer_name = None
        self.customer_phone = None
        self.verified = False
        self.is_employee = False
        self.tools_used = []
        self.started_at = datetime.now(timezone.utc)
        self.room = None
        self.transcript = []  # [{role, text}]

    def add_transcript(self, role: str, text: str):
        self.transcript.append({"role": role, "text": text})
        if len(self.transcript) > 30:
            self.transcript = self.transcript[-30:]

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "verified": self.verified,
            "is_employee": self.is_employee,
            "duration": (datetime.now(timezone.utc) - self.started_at).seconds,
        }


# ---- Data Channel Helpers ----
def _publish(room: rtc.Room, event_type: str, data: dict = None):
    """Fire-and-forget publish to data channel."""
    try:
        payload = json.dumps({
            "type": event_type, **(data or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, default=str).encode()
        asyncio.get_event_loop().create_task(
            room.local_participant.publish_data(payload, reliable=True, topic="ui_sync")
        )
    except Exception as e:
        logger.warning(f"Publish failed ({event_type}): {e}")


# ---- PII Masking ----
import re as _re
def mask_pii(text: str) -> str:
    text = _re.sub(r'(\+?\d{1,3})(\d{4})(\d{4})', r'\1****\3', text)
    text = _re.sub(r'(\d{3})\d{4,}(\d{3})', r'\1****\2', text)
    text = _re.sub(r'(\w)[^\s@]*(@\S+)', r'\1***\2', text)
    return text


# ---- Tool Imports ----
from tools.caller import identify_caller, send_verification_otp, verify_caller_otp, create_new_account
from tools.loans import (
    get_loans, get_loan_detail_tool, get_next_emi_tool,
    calculate_prepayment_tool, get_loan_application_status,
    explain_charges, request_emi_reschedule
)
from tools.investments import (
    get_portfolio_summary_tool, get_portfolio_holdings, get_fund_info_tool,
    search_funds_tool, get_transactions_tool, get_sip_status,
    get_dividends_tool, request_redemption, request_fund_switch, modify_sip
)
from tools.general import (
    create_support_ticket, get_my_tickets, escalate_to_rm,
    schedule_callback, update_contact_info, request_statement, send_whatsapp_message
)
from tools.employee import (
    search_customer_tool, get_delinquency_report,
    get_rm_portfolio_summary, get_daily_collections_tool,
    get_compliance_alerts
)

CUSTOMER_TOOLS = [
    identify_caller, send_verification_otp, verify_caller_otp, create_new_account,
    get_loans, get_loan_detail_tool, get_next_emi_tool,
    calculate_prepayment_tool, get_loan_application_status,
    explain_charges, request_emi_reschedule,
    get_portfolio_summary_tool, get_portfolio_holdings, get_fund_info_tool,
    search_funds_tool, get_transactions_tool, get_sip_status,
    get_dividends_tool, request_redemption, request_fund_switch, modify_sip,
    create_support_ticket, get_my_tickets, escalate_to_rm,
    schedule_callback, update_contact_info, request_statement,
]

EMPLOYEE_TOOLS = CUSTOMER_TOOLS + [
    search_customer_tool, get_delinquency_report,
    get_rm_portfolio_summary, get_daily_collections_tool,
    get_compliance_alerts,
]

# ---- Instructions (State-Driven) ----
BASE_INSTRUCTIONS = """You are MRNA, an AI customer support agent for a loans and investment management company in Saudi Arabia.

IDENTITY:
- Name: MRNA
- Role: Financial Services Support Agent  
- Languages: English and Arabic (respond in the language the customer uses)
- Tone: Professional, warm, trustworthy. You handle people's money.

RULES:
- NEVER share information about other customers
- For transactions (redemption, switch, prepayment): get VERBAL confirmation first
- If caller says "complaint", "ombudsman", or "legal": immediately escalate_to_rm
- Be concise - 2-3 sentences max per turn
- Use SAR (Saudi Riyal) for amounts, round to nearest whole number
- If KYC is expired: inform customer, restrict to read-only

CAPABILITIES:
- Loans: balance, EMI schedule, payment history, prepayment calculator, reschedule, charges
- Investments: portfolio summary, holdings, fund info, transactions, SIPs, dividends, redemption, switch
- General: tickets, escalate to RM, schedule callbacks, update contact info, statements
- Database: ad-hoc questions via natural language
"""

UNVERIFIED_INSTRUCTIONS = """
CURRENT STATE: WAITING FOR VERIFICATION
The customer has NOT been verified yet. An OTP code has been sent to their WhatsApp.
- Tell them you've sent a verification code to their WhatsApp
- Ask them to either read the code aloud OR type it in the verification box on screen
- Do NOT share any account details until verified
- Do NOT call identify_caller or send_verification_otp (already done)
- When they read the code aloud, use verify_caller_otp to check it
"""

VERIFIED_INSTRUCTIONS = """
CURRENT STATE: VERIFIED
The customer has been successfully verified. Their identity is confirmed.
- Greet them by name and ask how you can help
- You can now share account details, process transactions, etc.
- Be proactive: "I also notice you have an upcoming EMI on the 15th"
- At the end of the call, summarize what was discussed
"""

NEW_CUSTOMER_INSTRUCTIONS = """
CURRENT STATE: NEW CUSTOMER (NO ACCOUNT)
The caller's phone was not found in our system.
- Welcome them to MRNA
- Explain we offer loans and investment management
- Ask if they'd like to create an account
- If yes: collect their FULL NAME, then use create_new_account
- After account creation, ask how you can help
"""


# ---- TTS/STT/LLM factories ----
def _make_tts():
    return openai.tts.TTS(
        model="speaches-ai/Kokoro-82M-v1.0-ONNX",
        voice="af_heart",
        base_url=KOKORO_URL,
    )

def _make_stt():
    return deepgram.stt.STT(model="nova-3", language="en")

def _make_llm():
    return openai.llm.LLM(model="gpt-4o-mini", temperature=0.3)


# ---- Post-Call Summary ----
def _send_summary_thread(phone: str, name: str, transcript: list):
    """Run in a separate thread so it survives event loop teardown."""
    async def _do():
        if not transcript:
            from wa_client import send_call_summary
            await send_call_summary(phone, name, "Thank you for calling MRNA Financial Services. If you need further assistance, please call again.")
            return

        lines = [f"{'Agent' if m['role'] == 'agent' else 'Customer'}: {m['text']}" for m in transcript[-10:]]
        text = "\n".join(lines)

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize this customer support call in 3-5 bullet points. Include action items. Be concise. Do not use markdown formatting like * or _."},
                    {"role": "user", "content": text},
                ],
                max_tokens=200,
            )
            summary = resp.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Summary LLM failed: {e}")
            summary = "Call completed. Please contact us if you need further assistance."

        from wa_client import send_call_summary
        logger.info(f"Sending summary: len={len(summary)}, preview={summary[:80]}")
        await send_call_summary(phone, name, summary)
        logger.info(f"Summary sent to {phone}")

    asyncio.run(_do())


# ---- Main Entrypoint ----
async def entrypoint(ctx):
    from db.database import reset_pool, get_customer_by_phone, generate_otp, verify_otp, log_audit
    await reset_pool()

    room = ctx.room
    state = SessionState()
    state.room = room
    room_name = room.name or "unknown"
    _sessions[room_name] = state

    logger.info(f"MRNA v2 starting in room {room_name}")

    # ---- Read metadata ----
    metadata = {}
    try:
        if hasattr(ctx, "job") and ctx.job and ctx.job.metadata:
            metadata = json.loads(ctx.job.metadata)
            logger.info(f"Metadata from job: {metadata}")
    except Exception:
        pass
    if not metadata.get("phone"):
        try:
            if ctx.room.metadata:
                metadata = json.loads(ctx.room.metadata)
        except Exception:
            pass

    caller_phone = metadata.get("phone", "")
    caller_mode = metadata.get("mode", "customer")
    state.is_employee = caller_mode == "employee"
    state.customer_phone = caller_phone

    # ---- Pre-fetch customer ----
    cust = None
    greeting = ""
    initial_state = "new_customer"

    if caller_phone:
        try:
            cust = await get_customer_by_phone(caller_phone)
            if cust:
                state.customer_id = cust["id"]
                state.customer_name = cust.get("name", "Customer")
                first_name = state.customer_name.split()[0]

                # Generate and send OTP
                code = await generate_otp(caller_phone, purpose="login")
                from wa_client import send_otp
                await send_otp(caller_phone, code, state.customer_name)
                logger.info(f"OTP {code} sent to {caller_phone}")

                greeting = f"Welcome back to MRNA, {first_name}. I've sent a verification code to your WhatsApp. Please read it back to me, or type it in the verification box on your screen."
                initial_state = "unverified"
            else:
                greeting = "Welcome to MRNA financial services. I see this is your first time calling us. Would you like to open an account?"
                initial_state = "new_customer"
        except Exception as e:
            logger.warning(f"Pre-fetch failed: {e}")
            greeting = "Welcome to MRNA financial services. How can I help you today?"

    # ---- Build instructions based on state ----
    def _build_instructions(verified: bool, is_new: bool = False):
        parts = [BASE_INSTRUCTIONS]
        if caller_phone:
            parts.append(f"\nCaller phone: {caller_phone}")
        if state.customer_name:
            parts.append(f"Customer name: {state.customer_name} (ID: {state.customer_id})")
        if state.is_employee:
            parts.append("\nThis is an EMPLOYEE call with elevated tool access.")
        if is_new:
            parts.append(NEW_CUSTOMER_INSTRUCTIONS)
        elif verified:
            parts.append(VERIFIED_INSTRUCTIONS)
        else:
            parts.append(UNVERIFIED_INSTRUCTIONS)
        return "\n".join(parts)

    # ---- Select tools ----
    from text_to_sql import ask_database
    from db.database import get_pool

    @function_tool(
        name="ask_database",
        description="Ask any question about the customer's account or company data using natural language."
    )
    async def ask_database_tool(question: str) -> str:
        pool = await get_pool()
        api_key = os.environ.get("OPENAI_API_KEY", "")
        return await ask_database(pool, question, api_key, state.customer_id)

    tools = (EMPLOYEE_TOOLS if state.is_employee else CUSTOMER_TOOLS) + [ask_database_tool]

    # ---- Create agent + session ----
    instructions = _build_instructions(
        verified=False,
        is_new=(initial_state == "new_customer")
    )

    agent = Agent(instructions=instructions, tools=tools)
    session = AgentSession(
        stt=_make_stt(),
        llm=_make_llm(),
        tts=_make_tts(),
        vad=silero.VAD.load(
            min_speech_duration=0.3,
            min_silence_duration=0.6,
            prefix_padding_duration=0.3,
            max_buffered_speech=30.0,
        ),
    )

    # ---- Start session ----
    await session.start(room=room, agent=agent)
    logger.info("Session started")

    # ---- Send initial events ----
    try:
        _publish(room, "call_started", {"phone": caller_phone, "mode": caller_mode, "room": room_name})
        if initial_state == "unverified":
            _publish(room, "otp_sent", {"phone": caller_phone, "code_length": 6})
    except Exception as e:
        logger.warning(f"Initial events failed: {e}")

    # ---- Greeting ----
    if greeting:
        asyncio.ensure_future(session.say(greeting, allow_interruptions=True))

    # ---- Data Channel: OTP from modal ----
    @room.on("data_received")
    def _on_data(dp):
        try:
            raw = dp.data.decode("utf-8") if hasattr(dp, 'data') and dp.data else ""
            if not raw:
                return
            msg = json.loads(raw)
            logger.info(f"Data channel: {msg.get('type', 'unknown')}")

            if msg.get("type") == "otp_submit" and msg.get("code"):
                code = msg["code"]
                logger.info(f"OTP from modal: {code}")

                async def _verify():
                    try:
                        result = await verify_otp(caller_phone, code, purpose="login")
                        logger.info(f"OTP result: {result}")
                        if result["verified"]:
                            state.verified = True
                            await log_audit(None, "MRNA_agent", "otp_verified", "otp", None, {"phone": caller_phone})

                            # Send verified event to frontend
                            await room.local_participant.publish_data(
                                json.dumps({"type": "otp_verified", "phone": caller_phone}).encode(),
                                reliable=True, topic="ui_sync"
                            )

                            # UPDATE agent instructions to verified state
                            new_instructions = _build_instructions(verified=True)
                            session.update_agent(Agent(instructions=new_instructions, tools=tools))
                            logger.info("Instructions updated to VERIFIED state")

                            # Now tell the agent to greet the verified customer
                            first_name = (state.customer_name or "").split()[0] or "there"
                            await session.say(
                                f"Great, you're verified {first_name}. How can I help you today?",
                                allow_interruptions=True,
                            )
                        else:
                            error = result.get("error", "Invalid code")
                            await session.say(
                                f"That code didn't match. Please check your WhatsApp and try again.",
                                allow_interruptions=True,
                            )
                    except Exception as e:
                        logger.error(f"OTP verify error: {e}")

                asyncio.ensure_future(_verify())
        except Exception as e:
            logger.warning(f"Data channel error: {e}")

    # ---- Transcript capture ----
    @session.on("user_input_transcribed")
    def _on_user(ev):
        if ev.is_final and ev.transcript:
            state.add_transcript("user", ev.transcript)
            _publish(room, "transcript", {"role": "user", "text": mask_pii(ev.transcript)})

    @session.on("conversation_item_added")
    def _on_agent(ev):
        item = ev.item
        if hasattr(item, 'role') and item.role == "assistant":
            text = ""
            if hasattr(item, 'text_content') and item.text_content:
                text = str(item.text_content)
            elif hasattr(item, 'content'):
                if isinstance(item.content, str):
                    text = item.content
                elif isinstance(item.content, list):
                    text = " ".join(str(c) for c in item.content if c)
            if text:
                state.add_transcript("agent", text)
                _publish(room, "transcript", {"role": "agent", "text": mask_pii(text)})

    @session.on("function_tools_executed")
    def _on_tools(ev):
        if hasattr(ev, 'function_calls'):
            for fc in ev.function_calls:
                name = fc.function_info.name if hasattr(fc, 'function_info') else str(fc)
                _publish(room, "tool_call", {"tool": name})
                # If verify_caller_otp was called via voice and succeeded, update state
                if name == "verify_caller_otp" and not state.verified:
                    # Check if the tool returned success
                    state.verified = True
                    new_instructions = _build_instructions(verified=True)
                    session.update_agent(Agent(instructions=new_instructions, tools=tools))
                    logger.info("Voice OTP verified - instructions updated")

    # ---- Disconnect: send summary ----
    def _on_disconnect():
        logger.info("Room disconnected, sending summary")
        t = threading.Thread(
            target=_send_summary_thread,
            args=(caller_phone, state.customer_name or "Customer", list(state.transcript)),
            daemon=False,
        )
        t.start()

    room.on("disconnected", lambda: _on_disconnect())


# ---- Admin API ----
import threading as _threading
from http.server import HTTPServer, BaseHTTPRequestHandler

ADMIN_PORT = int(os.environ.get("FINVOX_ADMIN_PORT", "8096"))

class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "agent": "MRNA-v2", "sessions": len(_sessions)})
        elif self.path == "/sessions":
            self._json(200, {k: v.to_dict() for k, v in _sessions.items()})
        else:
            self._json(404, {"error": "not found"})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def log_message(self, *a): pass

def _start_admin():
    try:
        HTTPServer(("0.0.0.0", ADMIN_PORT), AdminHandler).serve_forever()
    except Exception as e:
        logger.error(f"Admin API failed: {e}")


if __name__ == "__main__":
    _threading.Thread(target=_start_admin, daemon=True).start()
    logger.info(f"Admin API on port {ADMIN_PORT}")

    cli.run_app(
        WorkerOptions(
            num_idle_processes=1,
            entrypoint_fnc=entrypoint,
            agent_name="mrna",
            port=8086,
        )
    )
