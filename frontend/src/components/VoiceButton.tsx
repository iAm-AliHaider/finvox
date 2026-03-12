"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import { Room, RoomEvent, Track } from "livekit-client";

type VoiceState = "idle" | "connecting" | "active" | "error";

export default function VoiceButton({ onCallStart, onCallEnd, onEvent, customerPhone, autoStart, onAutoStartConsumed, onRoomReady }: {
  onCallStart: () => void;
  onCallEnd: () => void;
  onEvent: (event: any) => void;
  customerPhone?: string;
  autoStart?: boolean;
  onAutoStartConsumed?: () => void;
  onRoomReady?: (room: Room) => void;
}) {
  const [state, setState] = useState<VoiceState>("idle");
  const roomRef = useRef<Room | null>(null);
  const audioElementsRef = useRef<Map<string, HTMLAudioElement>>(new Map());
  const btnRef = useRef<HTMLButtonElement>(null);

  // Cleanup audio elements on unmount
  useEffect(() => {
    return () => {
      audioElementsRef.current.forEach(el => {
        el.pause();
        el.srcObject = null;
      });
    };
  }, []);

  // Auto-start: simulate click so browser trusts it as user gesture
  useEffect(() => {
    if (autoStart && state === "idle" && btnRef.current) {
      btnRef.current.click();
      onAutoStartConsumed?.();
    }
  }, [autoStart, state, onAutoStartConsumed]);

  const startCall = useCallback(async () => {
    if (state === "active") {
      // End call
      if (roomRef.current) {
        await roomRef.current.disconnect();
        roomRef.current = null;
      }
      audioElementsRef.current.forEach(el => { el.pause(); el.remove(); });
      audioElementsRef.current.clear();
      setState("idle");
      onCallEnd();
      return;
    }

    setState("connecting");
    try {
      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: customerPhone || "", mode: "customer" }),
      });

      if (!res.ok) throw new Error("Token request failed");
      const { token, url } = await res.json();

      const room = new Room({ adaptiveStream: true, dynacast: true });
      roomRef.current = room;
      if (onRoomReady) onRoomReady(room);

      // Data channel events from agent
      room.on(RoomEvent.DataReceived, (data: Uint8Array, participant: any, kind: any, topic: string) => {
        if (topic === "ui_sync") {
          try { onEvent(JSON.parse(new TextDecoder().decode(data))); } catch {}
        }
      });

      // Attach agent audio when track arrives
      room.on(RoomEvent.TrackSubscribed, (track, publication) => {
        if (track.kind === Track.Kind.Audio) {
          const audioEl = document.createElement("audio");
          audioEl.autoplay = true;
          audioEl.style.display = "none";
          document.body.appendChild(audioEl);
          track.attach(audioEl);
          audioElementsRef.current.set(publication.trackSid, audioEl);
        }
      });

      room.on(RoomEvent.TrackUnsubscribed, (track, publication) => {
        const audioEl = audioElementsRef.current.get(publication.trackSid);
        if (audioEl) { track.detach(audioEl); audioEl.remove(); audioElementsRef.current.delete(publication.trackSid); }
      });

      room.on(RoomEvent.Disconnected, () => {
        setState("idle");
        onCallEnd();
        audioElementsRef.current.forEach(el => { el.pause(); el.remove(); });
        audioElementsRef.current.clear();
      });

      await room.connect(url, token);
      await room.startAudio();
      await room.localParticipant.setMicrophoneEnabled(true);

      // Attach existing remote audio
      room.remoteParticipants.forEach(p => {
        p.getTrackPublications().forEach(pub => {
          if (pub.isSubscribed && pub.track && pub.kind === Track.Kind.Audio) {
            const audioEl = document.createElement("audio");
            audioEl.autoplay = true;
            audioEl.style.display = "none";
            document.body.appendChild(audioEl);
            pub.track.attach(audioEl);
            audioElementsRef.current.set(pub.trackSid, audioEl);
          }
        });
      });

      setState("active");
      onCallStart();
    } catch (e: any) {
      console.error("Call error:", e);
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }, [state, customerPhone, onCallStart, onCallEnd, onEvent]);

  const cfg = {
    idle: { bg: "bg-blue-600 hover:bg-blue-700", text: "Start Call" },
    connecting: { bg: "bg-yellow-500 cursor-not-allowed", text: "Connecting..." },
    active: { bg: "bg-red-500 hover:bg-red-600", text: "End Call" },
    error: { bg: "bg-gray-400 cursor-not-allowed", text: "Error" },
  }[state];

  return (
    <button
      ref={btnRef}
      onClick={startCall}
      disabled={state === "connecting"}
      className={`${cfg.bg} text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all disabled:opacity-60`}
    >
      {state === "active" && <span className="w-2 h-2 rounded-full bg-white animate-pulse" />}
      {state === "idle" && (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none"/>
        </svg>
      )}
      {cfg.text}
    </button>
  );
}
