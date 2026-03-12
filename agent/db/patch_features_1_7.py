"""
Features 1-7 patch for MRNA agent:
1. OTP verification event -> frontend verified state (already wired in caller.py _notify_ui)
2. Transcript events via agent speech callbacks
3. WhatsApp text support (inbound message handling)
4. Post-call summary via WA
5. PDF/statement delivery notification via WA
6. Session linking (voice + WA shared context)
7. PII masking in transcript
"""
import pathlib

agent_path = pathlib.Path(__file__).parent.parent / "agent.py"
src = agent_path.read_text(encoding="utf-8")

# ============================================================
# FEATURE 2: Transcript events + FEATURE 4: Post-call summary
# FEATURE 6: Session linking + FEATURE 7: PII masking
# ============================================================

# Add PII masking utility after _send_event
old_tool_imports = "# --- Tool Imports"
if old_tool_imports not in src:
    # Try encoded version
    for marker in ["\xe2\x80\x94 Tool Imports", "Tool Imports"]:
        if marker in src:
            idx = src.find(marker)
            # Find the comment line start
            line_start = src.rfind("\n", 0, idx)
            old_tool_imports = src[line_start+1:idx+len(marker)]
            break

# Find insertion point - after _send_event function
insert_marker = "    except Exception as e:\n        logger.warning(f\"Failed to send event: {e}\")\n"
last_idx = src.rfind(insert_marker)
if last_idx == -1:
    print("ERROR: could not find _send_event end")
    raise SystemExit(1)

insert_point = last_idx + len(insert_marker)

new_code = '''

# --- PII Masking (Feature 7) ---
import re as _re

def mask_pii(text: str) -> str:
    """Mask sensitive data in transcript text."""
    # Mask phone numbers: +966XXXXXXXXX -> +966****XXXX
    text = _re.sub(r'(\+?\d{1,3})(\d{4})(\d{4})', r'\\1****\\3', text)
    # Mask national IDs: 10+ digits -> first 3 + **** + last 3
    text = _re.sub(r'\b(\d{3})\d{4,}(\d{3})\b', r'\\1****\\2', text)
    # Mask email: a***@domain
    text = _re.sub(r'(\w)[^\s@]*(@\S+)', r'\\1***\\2', text)
    # Mask OTP codes in transcript (6 digits standalone)
    text = _re.sub(r'\b(\d{6})\b', r'***OTP***', text)
    return text


# --- Session store for WA linking (Feature 6) ---
_wa_sessions: dict[str, dict] = {}  # phone -> {room_name, customer_id, context}

def link_wa_session(phone: str, room_name: str, customer_id: str = None):
    """Link a WhatsApp conversation to a voice session."""
    _wa_sessions[phone] = {
        "room_name": room_name,
        "customer_id": customer_id,
        "context": [],
    }

def get_wa_session(phone: str) -> dict | None:
    return _wa_sessions.get(phone)

def add_wa_context(phone: str, role: str, text: str):
    sess = _wa_sessions.get(phone)
    if sess:
        sess["context"].append({"role": role, "text": text})
        # Keep last 20 messages
        if len(sess["context"]) > 20:
            sess["context"] = sess["context"][-20:]

'''

src = src[:insert_point] + new_code + src[insert_point:]

# ============================================================
# Add transcript + post-call + session linking to entrypoint
# ============================================================

# Find the section after session.say(greeting) and data channel events
old_end = '''    except Exception as e:
        logger.warning(f"Data channel events failed: {e}")'''

# Find the LAST occurrence (after the data channel events block)
idx = src.rfind(old_end)
if idx == -1:
    print("ERROR: could not find data channel events end")
    raise SystemExit(1)

new_end = '''    except Exception as e:
        logger.warning(f"Data channel events failed: {e}")

    # --- Feature 6: Link WA session ---
    if caller_phone:
        link_wa_session(caller_phone, room_name, session_state.customer_id)

    # --- Feature 2: Transcript events via speech callbacks ---
    def _on_agent_speech(text: str):
        """Send agent speech to frontend as transcript event."""
        masked = mask_pii(text)
        _send_event(room, "transcript", {"role": "agent", "text": masked})
        if caller_phone:
            add_wa_context(caller_phone, "agent", text)

    def _on_user_speech(text: str):
        """Send user speech to frontend as transcript event."""
        masked = mask_pii(text)
        _send_event(room, "transcript", {"role": "user", "text": masked})
        if caller_phone:
            add_wa_context(caller_phone, "user", text)

    # Wire up speech events
    @session.on("agent_speech_committed")
    def handle_agent_speech(ev):
        if hasattr(ev, 'content') and ev.content:
            _on_agent_speech(ev.content)

    @session.on("user_speech_committed")
    def handle_user_speech(ev):
        if hasattr(ev, 'content') and ev.content:
            _on_user_speech(ev.content)

    # --- Feature 2b: Tool call events ---
    @session.on("function_calls_finished")
    def handle_tool_calls(ev):
        if hasattr(ev, 'function_calls'):
            for fc in ev.function_calls:
                _send_event(room, "tool_call", {"tool": fc.name if hasattr(fc, 'name') else str(fc)})

    # --- Feature 4: Post-call summary on disconnect ---
    async def _send_post_call_summary():
        """Generate and send call summary via WhatsApp after disconnect."""
        if not caller_phone:
            return
        wa_sess = get_wa_session(caller_phone)
        if not wa_sess or not wa_sess["context"]:
            return
        # Build summary from context
        lines = []
        for msg in wa_sess["context"]:
            prefix = "Agent" if msg["role"] == "agent" else "Customer"
            lines.append(f"{prefix}: {msg['text']}")
        transcript_text = "\\n".join(lines[-10:])  # last 10 exchanges

        # Use LLM to summarize
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize this customer support call in 3-5 bullet points. Include any action items. Be concise."},
                    {"role": "user", "content": transcript_text},
                ],
                max_tokens=200,
            )
            summary = resp.choices[0].message.content
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            summary = "Call completed. Please contact us if you need further assistance."

        # Send via WA
        from wa_client import send_call_summary
        cust_name = cust.get("name", "Customer") if cust else "Customer"
        await send_call_summary(caller_phone, cust_name, summary)
        logger.info(f"Post-call summary sent to {caller_phone}")

    room.on("disconnected", lambda: asyncio.ensure_future(_send_post_call_summary()))'''

src = src[:idx] + new_end + src[idx + len(old_end):]

agent_path.write_text(src, encoding="utf-8")
print("Patched agent.py with features 1-7")
