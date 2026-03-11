import asyncio, asyncpg
from datetime import datetime, timezone, timedelta

DB = "postgresql://neondb_owner:npg_laesRAW8Dui1@ep-plain-sound-aib5z9bz-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def main():
    conn = await asyncpg.connect(DB)
    db_now = await conn.fetchval("SELECT NOW()")
    py_now = datetime.now(timezone.utc)
    print(f"DB NOW:     {db_now}")
    print(f"Python NOW: {py_now}")
    print(f"Diff: {(db_now - py_now).total_seconds():.1f}s")

    row = await conn.fetchrow("SELECT * FROM finvox.otp_store ORDER BY created_at DESC LIMIT 1")
    if row:
        exp = row["expires_at"]
        print(f"expires_at:  {exp}")
        print(f"exp.tzinfo:  {exp.tzinfo}")
        print(f"py > exp?:   {py_now > exp}")
        # The issue: expires was set with Python utcnow() which is naive
        # but stored as TIMESTAMPTZ — Neon assumes UTC
        # Let's see created_at vs expires_at diff
        print(f"created_at:  {row['created_at']}")
        print(f"TTL:         {(exp - row['created_at']).total_seconds():.0f}s")
    
    await conn.close()

asyncio.run(main())
