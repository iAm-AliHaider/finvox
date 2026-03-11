"""Patch: inject create_customer into database.py at line 71"""
import pathlib

db_path = pathlib.Path(__file__).parent / "database.py"
lines = db_path.read_text(encoding="utf-8").splitlines(keepends=True)

new_func = '''
async def create_customer(name: str, phone: str, email: str = None, national_id: str = None, city: str = None) -> dict:
    """Create a new customer account. Returns the new customer dict."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Generate next ID
        row = await conn.fetchrow(
            "SELECT id FROM finvox.customers ORDER BY created_at DESC LIMIT 1"
        )
        if row:
            num = int(row["id"].replace("CUST", "")) + 1
        else:
            num = 1
        new_id = f"CUST{num:03d}"

        await conn.execute(
            """INSERT INTO finvox.customers (id, name, phone, email, national_id, city, kyc_status, tier, preferred_language, wa_verified, onboarded_at, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, 'pending', 'retail', 'en', true, CURRENT_DATE, NOW())""",
            new_id, name, phone, email, national_id, city
        )
        return {"id": new_id, "name": name, "phone": phone, "email": email, "tier": "retail", "kyc_status": "pending"}


'''

# Insert at line 71 (after "return True" and before OTP section)
lines.insert(70, new_func)
db_path.write_text("".join(lines), encoding="utf-8")
print("OK - create_customer injected")
