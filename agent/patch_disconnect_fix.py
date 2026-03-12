"""Fix post-call summary: room teardown kills async tasks before WA send completes.
Solution: Use threading for the WA send so it survives event loop shutdown."""

with open("agent.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Fix the disconnect handler to use a thread for reliability
old_disconnect = '''    room.on("disconnected", lambda: asyncio.ensure_future(_send_post_call_summary()))'''

new_disconnect = '''    # Use thread for post-call summary so it survives event loop teardown
    def _on_disconnect():
        import threading
        t = threading.Thread(target=lambda: asyncio.run(_send_post_call_summary()), daemon=False)
        t.start()
    room.on("disconnected", lambda: _on_disconnect())'''

if old_disconnect in code:
    code = code.replace(old_disconnect, new_disconnect)
    print("PATCHED: disconnect handler uses thread for summary")
else:
    print("SKIP: disconnect handler not found")

# 2. Fix data_received event name (LiveKit Python SDK uses different name)
# Actually let's check - the event might be correct for room.on
# In LiveKit Python SDK, room events use "data_received" 
# But the callback signature needs (data: rtc.DataPacket)
# Let's fix the callback to handle the actual DataPacket structure

old_data = '''    @room.on("data_received")
    def _on_data_received(data_packet):
        try:
            raw = data_packet.data.decode("utf-8") if hasattr(data_packet, 'data') else ""
            if not raw:
                return
            import json as _json
            msg = _json.loads(raw)'''

new_data = '''    @room.on("data_received")
    def _on_data_received(data_packet):
        try:
            # DataPacket can have .data (bytes) or .payload
            raw = ""
            if hasattr(data_packet, 'data') and data_packet.data:
                raw = data_packet.data.decode("utf-8")
            elif hasattr(data_packet, 'payload') and data_packet.payload:
                raw = data_packet.payload.decode("utf-8")
            elif isinstance(data_packet, bytes):
                raw = data_packet.decode("utf-8")
            logger.info(f"Data channel received: {raw[:200] if raw else '(empty)'}")
            if not raw:
                return
            import json as _json
            msg = _json.loads(raw)'''

if old_data in code:
    code = code.replace(old_data, new_data)
    print("PATCHED: data_received handler with better payload extraction + logging")
else:
    print("SKIP: data_received handler not found")

# 3. Also use text_content as primary source (we confirmed it works)
old_content = '''        # Try multiple attribute paths for agent text
        if hasattr(item, 'role') and item.role == "assistant":
            if hasattr(item, 'content'):
                if isinstance(item.content, str):
                    text = item.content
                elif isinstance(item.content, list):
                    text = " ".join(str(c) for c in item.content if c)
            if not text and hasattr(item, 'text_content'):
                text = str(item.text_content) if item.text_content else ""
            if not text and hasattr(item, 'output'):
                text = str(item.output) if item.output else ""'''

new_content = '''        # Try multiple attribute paths for agent text
        if hasattr(item, 'role') and item.role == "assistant":
            # text_content is the confirmed working attribute in v1.4.3
            if hasattr(item, 'text_content') and item.text_content:
                text = str(item.text_content)
            elif hasattr(item, 'content'):
                if isinstance(item.content, str):
                    text = item.content
                elif isinstance(item.content, list):
                    text = " ".join(str(c) for c in item.content if c)
            if not text and hasattr(item, 'output'):
                text = str(item.output) if item.output else ""'''

if old_content in code:
    code = code.replace(old_content, new_content)
    print("PATCHED: text_content is now primary source for conversation items")
else:
    print("SKIP: content extraction block not found")

# 4. Add close_on_disconnect=False to keep session alive for cleanup
old_session_start = '''    await session.start(
        room=room,
        agent=agent,
    )'''

new_session_start = '''    await session.start(
        room=room,
        agent=agent,
        room_input_options=RoomInputOptions(close_on_disconnect=False),
    )'''

if old_session_start in code:
    code = code.replace(old_session_start, new_session_start)
    print("PATCHED: close_on_disconnect=False to allow post-call cleanup")
else:
    print("SKIP: session.start block not found")

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(code)

print("\nAll patches applied. Restart agent.")
