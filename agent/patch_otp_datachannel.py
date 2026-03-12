"""
Patch 1: Frontend - handleOTPSubmit sends code via data channel
Patch 2: Agent - listens for otp_submit on data channel and auto-verifies
"""

# --- PATCH FRONTEND ---
with open("../frontend/src/app/page.tsx", "r", encoding="utf-8") as f:
    fe = f.read()

old_otp = """  const handleOTPSubmit = (code: string) => {
    setShowOTP(false);
    setVerified(true);
  };"""

new_otp = """  const handleOTPSubmit = (code: string) => {
    // Send OTP to agent via data channel so it can verify without voice
    if (roomRef.current && roomRef.current.localParticipant) {
      const payload = JSON.stringify({ type: "otp_submit", code });
      roomRef.current.localParticipant.publishData(
        new TextEncoder().encode(payload),
        { topic: "ui_sync", reliable: true }
      );
    }
    setShowOTP(false);
    // Don't set verified here - wait for otp_verified event from agent
  };"""

if old_otp in fe:
    fe = fe.replace(old_otp, new_otp)
    print("PATCHED frontend: handleOTPSubmit sends code via data channel")
else:
    print("SKIP frontend: handleOTPSubmit not found (already patched?)")

with open("../frontend/src/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(fe)

# --- PATCH AGENT ---
with open("agent.py", "r", encoding="utf-8") as f:
    ag = f.read()

# Find the data channel handler section - add OTP handling
# Look for the existing data_received handler or add one
old_transcript = '''    @session.on("user_input_transcribed")
    def handle_user_input(ev):'''

new_transcript = '''    # --- Data channel listener for OTP submit from frontend ---
    @room.on("data_received")
    def _on_data_received(data_packet):
        try:
            raw = data_packet.data.decode("utf-8") if hasattr(data_packet, 'data') else ""
            if not raw:
                return
            import json as _json
            msg = _json.loads(raw)
            if msg.get("type") == "otp_submit" and msg.get("code"):
                otp_code = msg["code"]
                logger.info(f"OTP submitted via modal: {otp_code}")
                # Inject into the conversation so the agent processes it
                asyncio.ensure_future(
                    session.generate_reply(
                        instructions=f"The customer just typed their OTP code in the verification modal: {otp_code}. Call verify_caller_otp with this code immediately. Do NOT ask them to read it out loud."
                    )
                )
        except Exception as e:
            logger.warning(f"Data channel parse error: {e}")

    @session.on("user_input_transcribed")
    def handle_user_input(ev):'''

if old_transcript in ag:
    ag = ag.replace(old_transcript, new_transcript)
    print("PATCHED agent: data channel OTP listener added")
else:
    print("SKIP agent: user_input_transcribed handler not found")

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(ag)

print("Done! Restart agent + redeploy frontend.")
