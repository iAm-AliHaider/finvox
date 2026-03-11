"""Add greeting + data channel events after session.start()."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "agent.py"
src = p.read_text(encoding="utf-8")

old = """    # Connect (blocks until session ends)
    await session.start(
        room=room,
        agent=agent,
    )"""

new = """    # Connect then greet
    await session.start(
        room=room,
        agent=agent,
    )

    logger.info("session.start() returned, sending greeting")

    # Greet the customer
    await session.say(greeting, allow_interruptions=True)

    # Send data channel events for frontend
    _otp_phone = caller_phone if otp_context else None
    try:
        _send_event(room, "call_started", {"phone": caller_phone, "mode": caller_mode, "room": room_name})
        if _otp_phone:
            _send_event(room, "otp_sent", {"phone": _otp_phone, "code_length": 6})
            logger.info(f"Sent otp_sent event for {_otp_phone}")
    except Exception as e:
        logger.warning(f"Data channel events failed: {e}")"""

if old not in src:
    print("ERROR: old block not found!")
    raise SystemExit(1)

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("Patched successfully")
