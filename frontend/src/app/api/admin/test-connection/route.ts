import { NextRequest, NextResponse } from "next/server";

const ADMIN = "http://127.0.0.1:8096";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const r = await fetch(`${ADMIN}/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}
