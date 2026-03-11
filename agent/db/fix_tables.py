"""Create missing tables in finvox schema."""
import asyncio
import asyncpg

DB_URL = "postgresql://neondb_owner:npg_laesRAW8Dui1@ep-plain-sound-aib5z9bz-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

TABLES = {
    "otp_store": """
        CREATE TABLE finvox.otp_store (
            id SERIAL PRIMARY KEY,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            purpose TEXT DEFAULT 'login',
            attempts INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT false,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """,
    "audit_log": """
        CREATE TABLE finvox.audit_log (
            id SERIAL PRIMARY KEY,
            customer_id TEXT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            details JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """,
    "notifications": """
        CREATE TABLE finvox.notifications (
            id SERIAL PRIMARY KEY,
            customer_id TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT DEFAULT 'in_app',
            read BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """,
    "compliance_flags": """
        CREATE TABLE finvox.compliance_flags (
            id SERIAL PRIMARY KEY,
            customer_id TEXT,
            flag_type TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            description TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            resolved_at TIMESTAMPTZ
        )
    """,
    "interactions": """
        CREATE TABLE finvox.interactions (
            id SERIAL PRIMARY KEY,
            customer_id TEXT NOT NULL,
            channel TEXT DEFAULT 'voice',
            duration INTEGER,
            summary TEXT,
            agent_notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """,
    "tickets": """
        CREATE TABLE finvox.tickets (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            category TEXT,
            subject TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            assigned_to TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """,
}


async def main():
    conn = await asyncpg.connect(DB_URL)
    
    for name, ddl in TABLES.items():
        exists = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='finvox' AND table_name=$1",
            name
        )
        if exists:
            print(f"  {name}: already exists")
        else:
            try:
                await conn.execute(ddl)
                print(f"  {name}: CREATED")
            except Exception as e:
                print(f"  {name}: ERROR - {e}")
    
    await conn.close()
    print("Done!")


asyncio.run(main())
