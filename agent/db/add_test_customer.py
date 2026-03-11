"""Add Boss's number as a test customer in finvox DB."""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()
from db.database import reset_pool, get_pool

async def main():
    await reset_pool()
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, name FROM finvox.customers WHERE phone = $1",
            "+966534006682"
        )
        if existing:
            print(f"Already exists: {existing['id']} - {existing['name']}")
            return

        await conn.execute("""
            INSERT INTO finvox.customers (
                id, name, phone, email, national_id, city, country,
                kyc_status, risk_profile, tier, preferred_language, wa_verified
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
        """,
            "C099", "Ali Haider", "+966534006682", "ali@finvox.test",
            "9999999999", "Riyadh", "Saudi Arabia",
            "valid", "aggressive", "premium", "en", True
        )
        print("Added Ali Haider as C099 (+966534006682)")

asyncio.run(main())
