import { NextRequest, NextResponse } from "next/server";

const LIVEKIT_URL = process.env.LIVEKIT_URL || "wss://agent-ls5zwwm3.livekit.cloud";
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY || "";
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET || "";

export async function POST(req: NextRequest) {
  try {
    const { phone, mode } = await req.json();

    const { AccessToken, RoomServiceClient, AgentDispatchClient } = await import("livekit-server-sdk");

    const roomName = `finvox-${Date.now()}`;
    const identity = `caller-${phone || "anonymous"}`;

    // Create token for the caller
    const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity,
      metadata: JSON.stringify({ phone: phone || "", mode: mode || "customer" }),
    });

    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      roomCreate: true,
    });

    const jwt = await token.toJwt();

    // Create the room first
    const httpUrl = LIVEKIT_URL.replace("wss://", "https://");
    const roomService = new RoomServiceClient(httpUrl, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
    
    try {
      await roomService.createRoom({
        name: roomName,
        metadata: JSON.stringify({ phone: phone || "", mode: mode || "customer" }),
      });
    } catch (e: any) {
      console.warn("Room create warning:", e.message);
    }

    // Dispatch the FinVox agent into the room
    try {
      const dispatch = new AgentDispatchClient(httpUrl, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
      await dispatch.createDispatch(roomName, "finvox", {
        metadata: JSON.stringify({ phone: phone || "", mode: mode || "customer" }),
      });
    } catch (e: any) {
      console.warn("Agent dispatch warning:", e.message);
    }

    return NextResponse.json({
      token: jwt,
      url: LIVEKIT_URL,
      room: roomName,
    });
  } catch (e: any) {
    console.error("Token error:", e);
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
