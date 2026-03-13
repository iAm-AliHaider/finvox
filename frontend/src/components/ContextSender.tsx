"use client";
import { useEffect, useRef } from "react";
import type { Room } from "livekit-client";

/**
 * Sends current UI context to the agent via data channel whenever it changes.
 * Agent uses this to know what the user is looking at.
 */
export default function ContextSender({
  room,
  activeTab,
  customerId,
  verified,
  callActive,
}: {
  room: Room | null;
  activeTab: string;
  customerId: string;
  verified: boolean;
  callActive: boolean;
}) {
  const lastSent = useRef("");

  useEffect(() => {
    if (!room || !callActive) return;

    const ctx = JSON.stringify({
      type: "context_sync",
      activeTab,
      customerId,
      verified,
      timestamp: new Date().toISOString(),
    });

    // Only send if changed
    if (ctx === lastSent.current) return;
    lastSent.current = ctx;

    const send = () => {
      try {
        if (room.localParticipant) {
          room.localParticipant.publishData(
            new TextEncoder().encode(ctx),
            { topic: "ui_sync", reliable: true }
          );
        }
      } catch {}
    };

    // Small delay to batch rapid changes
    const t = setTimeout(send, 100);
    return () => clearTimeout(t);
  }, [room, activeTab, customerId, verified, callActive]);

  return null;
}
