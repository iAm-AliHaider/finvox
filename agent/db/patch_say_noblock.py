"""Fix: don't await session.say() - fire as task, send events immediately."""
import pathlib
p = pathlib.Path(__file__).parent.parent / "agent.py"
src = p.read_text(encoding="utf-8")

old = '''    logger.info("session.start() returned, sending greeting")

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
        logger.warning(f"Data channel events failed: {e}")'''

new = '''    logger.info("session.start() returned, sending greeting and events")

    # Send data channel events FIRST (before greeting blocks)
    _otp_phone = caller_phone if otp_context else None
    try:
        await room.local_participant.publish_data(
            json.dumps({"type": "call_started", "phone": caller_phone, "mode": caller_mode, "room": room_name}).encode(),
            reliable=True, topic="ui_sync"
        )
        if _otp_phone:
            await room.local_participant.publish_data(
                json.dumps({"type": "otp_sent", "phone": _otp_phone, "code_length": 6}).encode(),
                reliable=True, topic="ui_sync"
            )
            logger.info(f"Sent otp_sent event for {_otp_phone}")
    except Exception as e:
        logger.warning(f"Data channel events failed: {e}")

    # Greet the customer (non-blocking - fire and forget)
    asyncio.ensure_future(session.say(greeting, allow_interruptions=True))'''

if old not in src:
    print("ERROR: block not found")
    raise SystemExit(1)

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("Patched: events before greeting, say() non-blocking")
