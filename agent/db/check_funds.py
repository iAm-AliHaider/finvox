import asyncio, sys
sys.path.insert(0, ".")
from database import get_pool
async def m():
    p = await get_pool()
    r = await p.fetch("SELECT conname, pg_get_constraintdef(oid) as def FROM pg_constraint WHERE conrelid='finvox.funds'::regclass AND contype='c'")
    for x in r: print(x["conname"], x["def"])
    await p.close()
asyncio.run(m())
