"""
Database Attacher — Connect ANY database, auto-discover schema,
generate dynamic voice tools and UI for customer support.

Plug any client DB → agent instantly becomes their support agent.
"""
import asyncio
import json
import logging
import re
from typing import Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger("mrna.db_attacher")


# ─── Schema Discovery ────────────────────────────────────────────────────────

async def discover_schema(pool, schema: str = "public") -> dict:
    """Auto-discover all tables, columns, types, and sample data."""
    tables = {}

    rows = await pool.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = $1 AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """, schema)

    for row in rows:
        tname = row["table_name"]
        try:
            tables[tname] = await _discover_table(pool, schema, tname)
        except Exception as e:
            logger.warning(f"Schema discovery failed for {tname}: {e}")
            tables[tname] = {"columns": [], "foreign_keys": [], "row_count": 0, "samples": []}

    return tables


async def _discover_table(pool, schema: str, tname: str) -> dict:
    # Columns
    cols = await pool.fetch("""
        SELECT column_name, data_type, is_nullable, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
    """, schema, tname)

    # Primary keys
    pks = await pool.fetch("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = $1 AND tc.table_name = $2 AND tc.constraint_type = 'PRIMARY KEY'
    """, schema, tname)
    pk_cols = {r["column_name"] for r in pks}

    # Foreign keys (best effort — Neon may restrict)
    fks = []
    try:
        fk_rows = await pool.fetch("""
            SELECT kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_col
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
            WHERE tc.table_schema = $1 AND tc.table_name = $2 AND tc.constraint_type = 'FOREIGN KEY'
        """, schema, tname)
        fks = [{"column": r["column_name"], "references": f'{r["ref_table"]}.{r["ref_col"]}'} for r in fk_rows]
    except Exception:
        pass

    # Row count
    try:
        cnt = await pool.fetchval(f'SELECT COUNT(*) FROM "{schema}"."{tname}"')
        row_count = int(cnt or 0)
    except Exception:
        row_count = 0

    # Sample rows (3)
    samples = []
    if row_count > 0:
        try:
            sample_rows = await pool.fetch(f'SELECT * FROM "{schema}"."{tname}" LIMIT 3')
            samples = [{k: _safe(v) for k, v in dict(r).items()} for r in sample_rows]
        except Exception:
            pass

    return {
        "columns": [
            {
                "name": c["column_name"],
                "type": c["data_type"],
                "nullable": c["is_nullable"] == "YES",
                "primary_key": c["column_name"] in pk_cols,
            }
            for c in cols
        ],
        "foreign_keys": fks,
        "row_count": row_count,
        "samples": samples,
    }


def _safe(v):
    if v is None or isinstance(v, (int, float, bool, str)):
        return v
    return str(v)


# ─── Schema Context (for LLM) ─────────────────────────────────────────────────

def build_schema_context(tables: dict, schema: str = "public") -> str:
    lines = [f"DATABASE SCHEMA ({schema}):\n"]
    for tname, info in tables.items():
        col_strs = []
        for c in info["columns"]:
            s = f'{c["name"]} {c["type"]}'
            if c["primary_key"]:
                s += " PK"
            col_strs.append(s)
        lines.append(f"TABLE {schema}.{tname} ({info['row_count']} rows):")
        lines.append(f"  {', '.join(col_strs)}")
        if info["foreign_keys"]:
            lines.append(f"  FK: {', '.join(fk['column']+' -> '+fk['references'] for fk in info['foreign_keys'])}")
        if info["samples"]:
            lines.append(f"  Sample: {json.dumps(info['samples'][0], default=str)}")
        lines.append("")
    return "\n".join(lines)


def generate_few_shots(tables: dict, schema: str) -> str:
    """Auto-generate Q&A examples from schema for LLM few-shot prompting."""
    examples = []
    for tname, info in tables.items():
        cols = [c["name"] for c in info["columns"]]

        # Count
        examples.append(f'Q: How many {tname}?\nSQL: SELECT COUNT(*) as total FROM {schema}.{tname}')

        # Name/title search
        name_cols = [c for c in cols if any(k in c.lower() for k in ["name", "title", "subject"])]
        if name_cols:
            examples.append(f'Q: Find {tname} named "example"\nSQL: SELECT * FROM {schema}.{tname} WHERE LOWER({name_cols[0]}) LIKE \'%example%\' LIMIT 10')

        # Status filter
        status_cols = [c for c in cols if any(k in c.lower() for k in ["status", "state", "type"])]
        if status_cols:
            examples.append(f'Q: Show active {tname}\nSQL: SELECT * FROM {schema}.{tname} WHERE {status_cols[0]} IN (\'active\',\'open\',\'pending\') LIMIT 20')

        # Latest by date
        date_cols = [c["name"] for c in info["columns"] if "date" in c["type"] or "timestamp" in c["type"]]
        if date_cols:
            examples.append(f'Q: Recent {tname}\nSQL: SELECT * FROM {schema}.{tname} ORDER BY {date_cols[0]} DESC LIMIT 10')

        # Sum money
        money_cols = [c for c in cols if any(k in c.lower() for k in ["amount", "total", "balance", "price"])]
        if money_cols:
            examples.append(f'Q: Total {money_cols[0]} in {tname}\nSQL: SELECT SUM({money_cols[0]}) as total FROM {schema}.{tname}')

    return "\n\n".join(examples[:25])


# ─── Safety ───────────────────────────────────────────────────────────────────

def is_safe_sql(sql: str) -> bool:
    cleaned = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL).strip().upper()
    if not (cleaned.startswith("SELECT") or cleaned.startswith("WITH")):
        return False
    for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]:
        if re.search(rf'\b{kw}\b', cleaned):
            return False
    return True


# ─── Main Attacher Class ──────────────────────────────────────────────────────

class DatabaseAttacher:
    """
    Attach any database → voice agent auto-discovers schema,
    answers questions in natural language, generates dynamic UI.
    """

    def __init__(self, config: dict):
        self.config = config
        self.pool = None
        self.tables = {}
        self.schema_context = ""
        self.few_shots = ""
        self.openai: Optional[AsyncOpenAI] = None
        self._connected = False

    async def connect(self):
        import asyncpg

        schema = self.config.get("schema", "public")

        async def _init(conn):
            await conn.execute(f"SET search_path TO {schema}")

        self.pool = await asyncpg.create_pool(
            self.config["database_url"],
            min_size=2, max_size=5,
            command_timeout=self.config.get("query_timeout", 10),
            init=_init,
        )

        logger.info(f"Discovering schema '{schema}'...")
        self.tables = await discover_schema(self.pool, schema)
        self.schema_context = build_schema_context(self.tables, schema)
        self.few_shots = generate_few_shots(self.tables, schema)
        self._connected = True

        api_key = self.config.get("openai_api_key")
        self.openai = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

        logger.info(f"Attached: {len(self.tables)} tables, {sum(len(t['columns']) for t in self.tables.values())} columns")

    async def close(self):
        if self.pool:
            await self.pool.close()

    # ─── Caller Identification ────────────────────────────────────────────

    async def identify_caller(self, phone: str) -> Optional[dict]:
        table = self.config.get("caller_table", "customers")
        field = self.config.get("caller_id_field", "phone")
        schema = self.config.get("schema", "public")
        try:
            row = await self.pool.fetchrow(
                f'SELECT * FROM "{schema}"."{table}" WHERE "{field}" = $1 LIMIT 1', phone
            )
            return {k: _safe(v) for k, v in dict(row).items()} if row else None
        except Exception as e:
            logger.warning(f"Caller lookup failed: {e}")
            return None

    # ─── Natural Language Query ───────────────────────────────────────────

    async def ask(self, question: str, caller_context: dict = None) -> dict:
        """NL question → SQL → execute → voice answer + UI payload."""
        schema = self.config.get("schema", "public")
        business = self.config.get("business_name", "the company")
        currency = self.config.get("currency", "SAR")
        biz_ctx = self.config.get("business_context", "")
        caller_str = f"\nCaller info: {json.dumps(caller_context, default=str)}" if caller_context else ""

        # Step 1: Generate SQL
        resp = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are a SQL expert for {business}. {biz_ctx}

{self.schema_context}

EXAMPLES:
{self.few_shots}

Rules:
- ONLY SELECT queries. Never modify data.
- Always prefix with {schema}.table_name
- LIMIT {self.config.get('max_rows', 50)} unless specified
- Return ONLY the SQL, no explanation{caller_str}"""},
                {"role": "user", "content": question},
            ],
            temperature=0, max_tokens=400,
        )

        sql = resp.choices[0].message.content.strip()
        if "```" in sql:
            m = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql, re.DOTALL)
            if m:
                sql = m.group(1)

        if not is_safe_sql(sql):
            return {"answer": "I can only look up information, not make changes.", "sql": sql, "data": [], "ui": None}

        # Step 2: Execute
        try:
            rows = await asyncio.wait_for(
                self.pool.fetch(sql), timeout=self.config.get("query_timeout", 10)
            )
            data = [{k: _safe(v) for k, v in dict(r).items()} for r in rows]
        except Exception as e:
            logger.warning(f"Query error: {e} | SQL: {sql}")
            return {"answer": "I couldn't retrieve that information right now.", "sql": sql, "data": [], "ui": None, "error": str(e)}

        # Step 3: Voice summary
        summary = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Summarize this as a helpful customer support response in 1-3 sentences for voice. Currency: {currency}. Company: {business}."},
                {"role": "user", "content": f"Question: {question}\nData ({len(data)} rows): {json.dumps(data[:5], default=str)}"},
            ],
            temperature=0.3, max_tokens=150,
        )
        answer = summary.choices[0].message.content.strip()

        # Step 4: Build UI
        ui = self._build_ui(question, data)

        return {"answer": answer, "sql": sql, "data": data, "ui": ui}

    # ─── Dynamic UI Builder ───────────────────────────────────────────────

    def _build_ui(self, question: str, data: list) -> Optional[dict]:
        if not data:
            return None

        cols = list(data[0].keys())
        title = question.strip().rstrip("?")[:45].title()

        # Single row → KV card
        if len(data) == 1:
            return {
                "title": title,
                "sections": [{
                    "type": "kv",
                    "data": {k.replace("_", " ").title(): str(v) for k, v in data[0].items() if v is not None},
                }],
            }

        # Multiple rows → table + optional chart
        sections = [
            {"type": "alert", "style": "info", "text": f"{len(data)} results found"},
            {
                "type": "table",
                "headers": [c.replace("_", " ").title() for c in cols],
                "rows": [[str(row.get(c, "")) for c in cols] for row in data[:20]],
            },
        ]

        # Add bar chart if we have numeric values
        num_cols = [c for c in cols if isinstance(data[0].get(c), (int, float))]
        label_cols = [c for c in cols if isinstance(data[0].get(c), str)]
        if num_cols and label_cols and len(data) <= 15:
            sections.append({
                "type": "chart",
                "chartType": "bar",
                "labels": [str(r.get(label_cols[0], "")) for r in data],
                "datasets": [{"label": num_cols[0].replace("_", " ").title(), "data": [r.get(num_cols[0], 0) for r in data]}],
            })

        return {"title": title, "sections": sections}

    # ─── Agent Instructions ───────────────────────────────────────────────

    def build_agent_instructions(self, caller: dict = None) -> str:
        business = self.config.get("business_name", "Customer Support")
        biz_ctx = self.config.get("business_context", "")
        currency = self.config.get("currency", "SAR")
        tables = ", ".join(self.tables.keys())

        caller_block = ""
        if caller:
            name = caller.get("name") or caller.get("full_name") or "Customer"
            caller_block = f"\nCurrent caller: {name}\nTheir data: {json.dumps(caller, default=str)}"

        return f"""You are the AI customer support agent for {business}.
{biz_ctx}

You have live access to the company database (tables: {tables}).
Currency: {currency}.

TOOLS AVAILABLE:
- query_database(question) — ask ANYTHING about the data in natural language
- lookup_caller_info(phone) — get full caller profile
- show_info_modal(title, sections) — display info on caller's screen
- navigate_to(tab) — guide caller to the right section

HOW TO HANDLE CALLS:
1. Greet the caller and identify them (use lookup_caller_info)
2. Listen to their question
3. Use query_database to look up relevant data
4. Give a short voice answer (1-3 sentences)
5. Show details on screen via show_info_modal

RULES:
- You can only READ data, never modify it
- Always verify caller identity before sharing sensitive info
- Keep voice responses concise — show details on screen
- If unsure, say so honestly{caller_block}"""

    def get_table_names(self) -> list:
        return list(self.tables.keys())

    def get_table_info(self, name: str) -> Optional[dict]:
        return self.tables.get(name)
