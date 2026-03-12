import asyncio, sys
sys.path.insert(0, ".")
from database import get_pool

async def main():
    pool = await get_pool()
    cols = await pool.fetch(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='finvox' ORDER BY table_name, ordinal_position"
    )
    current = ""
    for c in cols:
        if c["table_name"] != current:
            current = c["table_name"]
            print(f"\n{current}:")
        print(f"  {c['column_name']}")
    await pool.close()

asyncio.run(main())
