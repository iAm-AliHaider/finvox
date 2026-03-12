import asyncio, sys
sys.path.insert(0, ".")
from database import get_pool

async def main():
    p = await get_pool()
    # Check constraints on loans
    r = await p.fetch(
        "SELECT conname, pg_get_constraintdef(oid) as def FROM pg_catalog.pg_constraint "
        "WHERE conrelid = 'finvox.loans'::regclass"
    )
    for x in r:
        print(f"{x['conname']}: {x['def']}")

    # Check existing types in all constrained tables
    for tbl in ["loans", "tickets", "compliance_flags", "interactions", "transactions", "funds", "portfolios"]:
        try:
            r2 = await p.fetch(f"SELECT DISTINCT type FROM finvox.{tbl}")
            print(f"\n{tbl} types: {[x['type'] for x in r2]}")
        except:
            pass
    await p.close()

asyncio.run(main())
