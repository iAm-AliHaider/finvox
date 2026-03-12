"""Fix: VoiceButton and page.tsx use separate roomRefs.
OTP modal can't send data because page.tsx roomRef is always null.
Solution: VoiceButton exposes room via onRoomReady callback."""

# --- PATCH VoiceButton.tsx ---
with open("../frontend/src/components/VoiceButton.tsx", "r", encoding="utf-8") as f:
    vb = f.read()

# Add onRoomReady prop
old_props = """export default function VoiceButton({ onCallStart, onCallEnd, onEvent, customerPhone, autoStart, onAutoStartConsumed }: {
  onCallStart: () => void;
  onCallEnd: () => void;
  onEvent: (event: any) => void;
  customerPhone?: string;
  autoStart?: boolean;
  onAutoStartConsumed?: () => void;
})"""

new_props = """export default function VoiceButton({ onCallStart, onCallEnd, onEvent, customerPhone, autoStart, onAutoStartConsumed, onRoomReady }: {
  onCallStart: () => void;
  onCallEnd: () => void;
  onEvent: (event: any) => void;
  customerPhone?: string;
  autoStart?: boolean;
  onAutoStartConsumed?: () => void;
  onRoomReady?: (room: Room) => void;
})"""

if old_props in vb:
    vb = vb.replace(old_props, new_props)
    print("PATCHED VoiceButton: added onRoomReady prop")
else:
    print("SKIP VoiceButton: props block not found")

# Add onRoomReady call after room connect
# Find where room connects and add the callback
old_connect = "      roomRef.current = room;"
new_connect = "      roomRef.current = room;\n      if (onRoomReady) onRoomReady(room);"

if old_connect in vb:
    # Only replace the first occurrence (before room.on events)
    vb = vb.replace(old_connect, new_connect, 1)
    print("PATCHED VoiceButton: onRoomReady called after room creation")
else:
    print("SKIP VoiceButton: roomRef assignment not found")

with open("../frontend/src/components/VoiceButton.tsx", "w", encoding="utf-8") as f:
    f.write(vb)

# --- PATCH page.tsx ---
with open("../frontend/src/app/page.tsx", "r", encoding="utf-8") as f:
    pg = f.read()

# Fix handleOTPSubmit to use the shared room ref
old_otp_handler = """  const handleOTPSubmit = (code: string) => {
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

new_otp_handler = """  const handleOTPSubmit = (code: string) => {
    // Send OTP to agent via data channel so it can verify without voice
    const room = roomRef.current;
    if (room && room.localParticipant) {
      const payload = JSON.stringify({ type: "otp_submit", code });
      room.localParticipant.publishData(
        new TextEncoder().encode(payload),
        { topic: "ui_sync", reliable: true }
      );
      console.log("[MRNA] OTP sent via data channel:", code);
    } else {
      console.warn("[MRNA] No room/localParticipant for OTP submit, room=", room);
    }
    setShowOTP(false);
    // Don't set verified here - wait for otp_verified event from agent
  };"""

if old_otp_handler in pg:
    pg = pg.replace(old_otp_handler, new_otp_handler)
    print("PATCHED page.tsx: handleOTPSubmit with logging")
else:
    print("SKIP page.tsx: handleOTPSubmit not found")

# Add onRoomReady to VoiceButton usage
old_voice_btn = """          <VoiceButton
            onCallStart={() => setCallActive(true)}
            onCallEnd={() => { setCallActive(false); setAutoCall(false); }}
            onEvent={handleVoiceEvent}
            customerPhone={phone}
            autoStart={autoCall}
            onAutoStartConsumed={() => setAutoCall(false)}
          />"""

new_voice_btn = """          <VoiceButton
            onCallStart={() => setCallActive(true)}
            onCallEnd={() => { setCallActive(false); setAutoCall(false); }}
            onEvent={handleVoiceEvent}
            customerPhone={phone}
            autoStart={autoCall}
            onAutoStartConsumed={() => setAutoCall(false)}
            onRoomReady={(room: any) => { roomRef.current = room; }}
          />"""

if old_voice_btn in pg:
    pg = pg.replace(old_voice_btn, new_voice_btn)
    print("PATCHED page.tsx: VoiceButton now passes room to parent roomRef")
else:
    print("SKIP page.tsx: VoiceButton usage not found")

with open("../frontend/src/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(pg)

print("\nDone! Rebuild + redeploy frontend.")
