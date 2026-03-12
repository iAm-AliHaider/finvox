import asyncio, sys, pathlib
sys.path.insert(0, ".")
from database import get_pool

async def check():
    p = await get_pool()
    for tbl in ["compliance_flags", "tickets", "interactions"]:
        r = await p.fetch(f"SELECT conname, pg_get_constraintdef(oid) as def FROM pg_constraint WHERE conrelid='finvox.{tbl}'::regclass AND contype='c'")
        for x in r: print(f"{tbl}: {x['conname']} = {x['def']}")
    await p.close()

asyncio.run(check())
