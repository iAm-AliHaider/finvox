"""Deploy FinVox schema and seed data to Neon Postgres."""
import asyncio
import asyncpg
import sys

DATABASE_URL = "postgresql://neondb_owner:npg_laesRAW8Dui1@ep-plain-sound-aib5z9bz-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def main():
    print("Connecting to Neon...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Drop existing schema for clean start
        print("Dropping existing finvox schema...")
        await conn.execute("DROP SCHEMA IF EXISTS finvox CASCADE")

        # Run schema
        print("Creating schema...")
        with open("schema.sql", "r") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)
        print("Schema created (20 tables)")

        # Run seed
        print("Seeding data...")
        with open("seed.sql", "r") as f:
            seed_sql = f.read()
        await conn.execute(seed_sql)
        print("Seed data inserted")

        # Verify
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'finvox' ORDER BY table_name
        """)
        print(f"\nTables created: {len(tables)}")
        for t in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM finvox.{t['table_name']}")
            print(f"  {t['table_name']}: {count} rows")

    finally:
        await conn.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
