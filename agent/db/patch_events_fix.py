"""Fix speech event handlers to use correct v1.4.3 event names and fields."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "agent.py"
src = p.read_text(encoding="utf-8")

old_events = '''    # --- Feature 2: Transcript events via speech callbacks ---
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
                _send_event(room, "tool_call", {"tool": fc.name if hasattr(fc, 'name') else str(fc)})'''

new_events = '''    # --- Feature 2: Transcript events via v1.4.3 event API ---
    @session.on("user_input_transcribed")
    def handle_user_input(ev):
        if ev.is_final and ev.transcript:
            masked = mask_pii(ev.transcript)
            _send_event(room, "transcript", {"role": "user", "text": masked})
            if caller_phone:
                add_wa_context(caller_phone, "user", ev.transcript)

    @session.on("conversation_item_added")
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
                    add_wa_context(caller_phone, "agent", text)

    # --- Feature 2b: Tool call events ---
    @session.on("function_tools_executed")
    def handle_tool_calls(ev):
        if hasattr(ev, 'function_calls'):
            for fc in ev.function_calls:
                name = fc.function_info.name if hasattr(fc, 'function_info') else str(fc)
                _send_event(room, "tool_call", {"tool": name})'''

if old_events not in src:
    print("ERROR: old events block not found")
    raise SystemExit(1)

src = src.replace(old_events, new_events, 1)
p.write_text(src, encoding="utf-8")
print("Fixed event handlers for v1.4.3")
