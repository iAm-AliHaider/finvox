"""
Client Configuration — Define attached databases for customer support.

Each client config is a JSON file in the configs/ directory.
The agent loads the active config on startup.

Example config (configs/acme_corp.json):
{
    "business_name": "Acme Corp",
    "business_type": "E-commerce",
    "business_context": "Online electronics retailer in Saudi Arabia",
    "greeting": "Welcome to Acme Corp! How can I help you today?",
    "currency": "SAR",
    "language": "en",
    "database_url": "postgresql://user:pass@host/db?sslmode=require",
    "schema": "public",
    "caller_table": "customers",
    "caller_id_field": "phone",
    "caller_name_field": "name",
    "otp_enabled": true,
    "branding": {
        "primary_color": "#2563eb",
        "logo_url": "https://example.com/logo.png",
        "company_short": "Acme"
    },
    "max_rows": 50,
    "query_timeout": 10
}
"""
import json
import os
import logging

logger = logging.getLogger("mrna.config")

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")
ACTIVE_CONFIG_FILE = os.path.join(CONFIGS_DIR, "_active.txt")


def ensure_configs_dir():
    os.makedirs(CONFIGS_DIR, exist_ok=True)


def list_configs() -> list:
    """List all available client configs."""
    ensure_configs_dir()
    return [f.replace(".json", "") for f in os.listdir(CONFIGS_DIR)
            if f.endswith(".json") and not f.startswith("_")]


def load_config(name: str) -> dict:
    """Load a client config by name."""
    ensure_configs_dir()
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(name: str, config: dict):
    """Save a client config."""
    ensure_configs_dir()
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved config: {name}")


def get_active_config_name() -> str:
    """Get the name of the currently active config."""
    ensure_configs_dir()
    if os.path.exists(ACTIVE_CONFIG_FILE):
        with open(ACTIVE_CONFIG_FILE, "r") as f:
            return f.read().strip()
    # Default: MRNA's own config
    return "mrna_default"


def set_active_config(name: str):
    """Set the active client config."""
    ensure_configs_dir()
    # Verify it exists
    path = os.path.join(CONFIGS_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config '{name}' not found")
    with open(ACTIVE_CONFIG_FILE, "w") as f:
        f.write(name)
    logger.info(f"Active config set to: {name}")


def load_active_config() -> dict:
    """Load the currently active client config."""
    name = get_active_config_name()
    return load_config(name)


# Default MRNA config (for when no client is attached)
MRNA_DEFAULT = {
    "business_name": "MRNA Financial Services",
    "business_type": "Financial Services",
    "business_context": "Loans, investments, portfolio management for Saudi Arabian customers",
    "greeting": "Welcome to MRNA Financial Services! How can I help you today?",
    "currency": "SAR",
    "language": "en",
    "database_url": os.environ.get("DATABASE_URL", ""),
    "schema": "finvox",
    "caller_table": "customers",
    "caller_id_field": "phone",
    "caller_name_field": "name",
    "otp_enabled": True,
    "branding": {
        "primary_color": "#2563eb",
        "logo_url": "",
        "company_short": "MRNA"
    },
    "max_rows": 50,
    "query_timeout": 10,
}


def create_default_config():
    """Create the default MRNA config if it doesn't exist."""
    ensure_configs_dir()
    path = os.path.join(CONFIGS_DIR, "mrna_default.json")
    if not os.path.exists(path):
        save_config("mrna_default", MRNA_DEFAULT)
        set_active_config("mrna_default")
