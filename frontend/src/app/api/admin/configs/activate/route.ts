import { NextRequest, NextResponse } from "next/server";

const ADMIN = "http://127.0.0.1:8096";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const r = await fetch(`${ADMIN}/configs/activate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return NextResponse.json(await r.json(), { status: r.status });
}
