"""
Dynamic Database Tools — Auto-generated voice tools from attached database.
These tools are created at runtime based on the schema discovery.
"""
import json
import logging
from livekit.agents.llm import function_tool

logger = logging.getLogger("mrna.tools.dynamic_db")

# Global reference to the attacher (set by agent.py on startup)
_attacher = None
_ui_publish = None  # function to publish UI events


def init(attacher, ui_publish_fn):
    """Initialize with the active database attacher."""
    global _attacher, _ui_publish
    _attacher = attacher
    _ui_publish = ui_publish_fn


def _send_modal(title, sections):
    """Send a DynamicModal to the frontend."""
    if _ui_publish:
        _ui_publish("show_modal", {"title": title, "sections": sections})


@function_tool(
    name="query_database",
    description="Query the attached database using natural language. Use this to look up ANY customer information — orders, account details, billing, products, status, history, etc. The question will be converted to SQL automatically."
)
async def query_database(question: str) -> str:
    """Ask any question about the database in natural language."""
    if not _attacher:
        return "Database is not connected. Please try again later."

    try:
        result = await _attacher.ask(question)

        # Show UI modal if we have data
        if result.get("ui"):
            _send_modal(result["ui"]["title"], result["ui"]["sections"])

        # Return voice-friendly answer
        if result.get("error"):
            return f"I encountered an issue looking that up. {result['answer']}"

        row_count = len(result.get("data", []))
        if row_count > 0:
            return f"{result['answer']} I've displayed the details on your screen."
        else:
            return result["answer"]

    except Exception as e:
        logger.error(f"query_database error: {e}")
        return "I'm having trouble accessing the database right now. Please try again."


@function_tool(
    name="lookup_caller_info",
    description="Look up the current caller's full profile and account details from the database."
)
async def lookup_caller_info(phone: str) -> str:
    """Look up caller details by phone number."""
    if not _attacher:
        return "Database not connected."

    try:
        caller = await _attacher.identify_caller(phone)
        if caller:
            # Show profile modal
            _send_modal("Customer Profile", [
                {
                    "type": "kv",
                    "data": {
                        k.replace("_", " ").title(): str(v)
                        for k, v in caller.items()
                        if v is not None and k not in ("password", "password_hash", "token", "secret")
                    },
                }
            ])

            name = caller.get("name", caller.get("full_name", "Customer"))
            return f"Found customer: {name}. Profile displayed on screen."
        else:
            return "No account found for this phone number."
    except Exception as e:
        logger.error(f"lookup_caller error: {e}")
        return "Could not look up caller information."


@function_tool(
    name="list_database_tables",
    description="List all available tables in the attached database. Use this to understand what data is available."
)
async def list_database_tables() -> str:
    """List all tables in the database."""
    if not _attacher:
        return "Database not connected."

    tables = _attacher.get_table_names()
    info_parts = []
    for t in tables:
        ti = _attacher.get_table_info(t)
        cols = [c["name"] for c in ti["columns"]]
        info_parts.append(f"{t} ({ti['row_count']} rows): {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")

    _send_modal("Database Tables", [
        {"type": "alert", "style": "info", "text": f"{len(tables)} tables available"},
        {"type": "table",
         "headers": ["Table", "Rows", "Key Columns"],
         "rows": [
             [t, str(_attacher.get_table_info(t)["row_count"]),
              ", ".join(c["name"] for c in _attacher.get_table_info(t)["columns"][:4])]
             for t in tables
         ]},
    ])

    return f"The database has {len(tables)} tables: {', '.join(tables)}. Details shown on screen."


# Export all tools as a list for the agent
DYNAMIC_TOOLS = [query_database, lookup_caller_info, list_database_tables]
