"""FinVox - Voice-First Financial Services Support Agent."""
import os
import sys
import json
import logging
import asyncio
from datetime import datetime

from livekit import rtc
from livekit.agents import (
    Agent, AgentSession, WorkerOptions, cli,
    RoomInputOptions,
)
from livekit.agents.llm import ChatContext
from livekit.agents import function_tool
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("finvox")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# TTS - Kokoro via Speaches (port 8000, $0)
KOKORO_URL = os.environ.get("KOKORO_URL", "http://localhost:8000/v1")

# Session state per room
_sessions = {}


class FinVoxSession:
    """Tracks state for a single call."""
    def __init__(self):
        self.customer_id = None
        self.customer_name = None
        self.customer_phone = None
        self.verified = False
        self.is_employee = False
        self.tools_used = []
        self.started_at = datetime.utcnow()
        self.room = None
        self.participant_identity = None

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "verified": self.verified,
            "is_employee": self.is_employee,
            "tools_used": self.tools_used,
            "duration": (datetime.utcnow() - self.started_at).seconds,
        }


def _send_ui(room: rtc.Room, component: str, props: dict):
    """Send UI update to frontend via data channel."""
    try:
        payload = json.dumps({
            "type": "ui_update",
            "component": component,
            "props": props,
            "timestamp": datetime.utcnow().isoformat(),
        }, default=str)

        asyncio.get_event_loop().create_task(
            room.local_participant.publish_data(
                payload.encode(), reliable=True, topic="ui_sync"
            )
        )
    except Exception as e:
        logger.warning(f"Failed to send UI update: {e}")


def _send_event(room: rtc.Room, event_type: str, data: dict = None):
    """Send event to frontend."""
    try:
        payload = json.dumps({
            "type": event_type,
            **(data or {}),
            "timestamp": datetime.utcnow().isoformat(),
        }, default=str)

        asyncio.get_event_loop().create_task(
            room.local_participant.publish_data(
                payload.encode(), reliable=True, topic="ui_sync"
            )
        )
    except Exception as e:
        logger.warning(f"Failed to send event: {e}")


# â”€â”€â”€ Tool Imports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
    schedule_callback, update_contact_info, request_statement
)
from tools.employee import (
    search_customer_tool, get_delinquency_report,
    get_rm_portfolio_summary, get_daily_collections_tool,
    get_compliance_alerts
)

# All customer-facing tools
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

# Additional employee tools
EMPLOYEE_TOOLS = CUSTOMER_TOOLS + [
    search_customer_tool, get_delinquency_report,
    get_rm_portfolio_summary, get_daily_collections_tool,
    get_compliance_alerts,
]

SYSTEM_PROMPT = """You are FinVox, an AI-powered customer support agent for a loans and investment management company in Saudi Arabia.

IDENTITY:
- Name: FinVox
- Role: Financial Services Support Agent
- Languages: English and Arabic (respond in the language the customer uses)
- Tone: Professional, warm, and reassuring. You handle people's money - be trustworthy.

CALL FLOW FOR EXISTING CUSTOMERS:
1. Greet the caller warmly
2. IMMEDIATELY use identify_caller with their phone number (from metadata)
3. If found, use send_verification_otp to send an OTP to their WhatsApp
4. Ask them to read back the OTP code they received
5. Use verify_caller_otp to confirm the code
6. Once verified, assist with their request
7. At the end, summarize what was discussed

CALL FLOW FOR NEW CUSTOMERS (phone not found):
1. When identify_caller returns "No account found", tell the caller they don't have an account yet
2. Ask if they would like to create one - explain FinVox offers loans and investment management
3. If yes, collect their FULL NAME
4. Use send_verification_otp with their phone to send a WhatsApp OTP
5. Ask them to read back the code
6. Use verify_caller_otp to confirm
7. Use create_new_account with their name, phone, and any other info they provide
8. Welcome them and explain next steps (KYC submission, available services)

IMPORTANT - IMMEDIATE ACTION ON CALL START:
- You have the caller's phone number from metadata. Use identify_caller RIGHT AWAY - do not wait for them to tell you their number.
- After greeting, your very first action must be identify_caller.

RULES:
- ALWAYS verify identity before sharing ANY account details (loans, balances, portfolio)
- For transactions (redemption, switch, prepayment): get VERBAL confirmation before creating the request
- If caller says "complaint", "ombudsman", or "legal": immediately escalate_to_rm
- Mask full account numbers in speech - say "account ending in 4567"
- If KYC is expired: inform customer and restrict to read-only. No transactions.
- Be concise in voice responses - 2-3 sentences max per turn
- Use SAR (Saudi Riyal) for all amounts
- Round amounts to nearest whole number in speech

COMPLIANCE:
- Never share information about other customers
- Never execute transactions without verbal confirmation
- Log all actions via audit trail (tools do this automatically)
- If unsure about any request, escalate to relationship manager

CAPABILITIES:
- Loans: Check balance, EMI schedule, payment history, prepayment calculator, reschedule, explain charges
- Investments: Portfolio summary, holdings, fund info, transactions, SIPs, dividends, redemption, switch
- General: Create tickets, escalate to RM, schedule callbacks, update contact info, request statements
- Database: Can answer ad-hoc questions about the customer's account using natural language

PERSONALITY:
- Empathetic when discussing financial difficulties
- Confident when explaining products and returns
- Patient with elderly or confused callers
- Proactive in offering relevant information (e.g., "I also notice you have an upcoming EMI on the 15th")
"""


def _make_tts():
    """Create TTS - Kokoro via Speaches ($0)."""
    return openai.tts.TTS(
        model="speaches-ai/Kokoro-82M-v1.0-ONNX",
        voice="af_heart",
        base_url=KOKORO_URL,
    )


def _make_stt():
    """Create STT - Deepgram Nova-3."""
    return deepgram.stt.STT(
        model="nova-3",
        language="en",
    )


def _make_llm():
    """Create LLM - GPT-4o-mini."""
    return openai.llm.LLM(
        model="gpt-4o-mini",
        temperature=0.3,
    )


async def entrypoint(ctx):
    """Main agent entrypoint."""
    from db.database import reset_pool
    await reset_pool()

    room = ctx.room
    session_state = FinVoxSession()
    session_state.room = room

    room_name = room.name if room else "unknown"
    _sessions[room_name] = session_state

    logger.info(f"FinVox agent starting in room {room_name}")

    # Read metadata for caller info
    metadata = {}
    try:
        if ctx.room.metadata:
            metadata = json.loads(ctx.room.metadata)
    except Exception:
        pass

    caller_phone = metadata.get("phone", "")
    caller_mode = metadata.get("mode", "customer")  # "customer" or "employee"
    session_state.is_employee = caller_mode == "employee"

    if caller_phone:
        session_state.customer_phone = caller_phone

    # Select tools based on mode
    tools = EMPLOYEE_TOOLS if session_state.is_employee else CUSTOMER_TOOLS

    # Build dynamic instructions
    full_instructions = SYSTEM_PROMPT
    if caller_phone:
        full_instructions += f"\n\nThe caller's phone number is {caller_phone}. Use identify_caller to look them up."
    if session_state.is_employee:
        full_instructions += "\n\nThis is an EMPLOYEE call. They have access to elevated tools like search_customer, delinquency_report, daily_collections, compliance_alerts, and RM portfolio views."

    # NL2SQL tool
    from text_to_sql import ask_database
    from db.database import get_pool

    @function_tool(
        name="ask_database",
        description="Ask any question about the customer's account or company data using natural language. Use this for questions not covered by other tools."
    )
    async def ask_database_tool(question: str) -> str:
        pool = await get_pool()
        api_key = os.environ.get("OPENAI_API_KEY", "")
        return await ask_database(pool, question, api_key, session_state.customer_id)

    all_tools = tools + [ask_database_tool]

    agent = Agent(
        instructions=full_instructions,
        tools=all_tools,
    )

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

    # Connect
    await session.start(
        room=room,
        agent=agent,
    )

    # Send initial UI state (after connecting)
    _send_event(room, "call_started", {
        "phone": caller_phone,
        "mode": caller_mode,
        "room": room_name,
    })

    # Pre-fetch customer to personalize greeting
    from db.database import get_customer_by_phone as _lookup
    greeting = "Welcome to FinVox financial services. How can I help you today?"
    if caller_phone:
        try:
            cust = await _lookup(caller_phone)
            if cust:
                name = cust.get("name", "").split()[0]  # First name
                session_state.customer_id = cust["id"]
                session_state.customer_phone = caller_phone
                greeting = f"Welcome back to FinVox, {name}. I have your account pulled up. For your security, I will send a verification code to your WhatsApp. One moment."
            else:
                greeting = f"Welcome to FinVox financial services. I see this is your first time calling us. Would you like to open an account? It only takes a minute and I can get you started right over the phone."
        except Exception as e:
            logger.warning(f"Pre-fetch failed: {e}")
            greeting = "Welcome to FinVox financial services. Let me look up your account."

    await session.say(greeting)

    logger.info(f"FinVox agent ready in room {room_name}")


# â”€â”€â”€ Admin API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

ADMIN_PORT = int(os.environ.get("FINVOX_ADMIN_PORT", "8096"))


class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "agent": "finvox", "sessions": len(_sessions)})
        elif self.path == "/sessions":
            data = {k: v.to_dict() for k, v in _sessions.items()}
            self._json(200, data)
        else:
            self._json(404, {"error": "not found"})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs


def _start_admin():
    try:
        server = HTTPServer(("0.0.0.0", ADMIN_PORT), AdminHandler)
        logger.info(f"Admin API on port {ADMIN_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Admin API failed: {e}")


if __name__ == "__main__":
    # Start admin API in background thread
    admin_thread = threading.Thread(target=_start_admin, daemon=True)
    admin_thread.start()

    cli.run_app(
        WorkerOptions(num_idle_processes=1, 
            entrypoint_fnc=entrypoint,
            agent_name="finvox",
            port=8086,
        )
    )










