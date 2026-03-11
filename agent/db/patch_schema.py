"""Patch all table references to use explicit finvox. schema prefix."""
import pathlib, re

db_path = pathlib.Path(__file__).parent / "database.py"
content = db_path.read_text(encoding="utf-8")

# Tables in finvox schema
TABLES = [
    "customers", "otp_store", "loans", "loan_payments", "loan_applications",
    "funds", "portfolios", "holdings", "transactions", "sips", "dividends",
    "relationship_managers", "bank_accounts", "documents", "statements",
    "tickets", "interactions", "compliance_flags", "notifications", "audit_log"
]

count = 0
for table in TABLES:
    # Match FROM/JOIN/INTO/UPDATE/DELETE FROM table_name but NOT already prefixed
    # Patterns: FROM table, JOIN table, INTO table, UPDATE table, DELETE FROM table, TABLE table
    for pattern in [
        rf'(?<!\.)(?<!\w)(FROM\s+){table}(?!\w)',
        rf'(?<!\.)(?<!\w)(JOIN\s+){table}(?!\w)',
        rf'(?<!\.)(?<!\w)(INTO\s+){table}(?!\w)',
        rf'(?<!\.)(?<!\w)(UPDATE\s+){table}(?!\w)',
        rf'(?<!\.)(?<!\w)(TABLE\s+){table}(?!\w)',
    ]:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            new_content = re.sub(pattern, rf'\1finvox.{table}', content, flags=re.IGNORECASE)
            if new_content != content:
                count += len(matches)
                content = new_content

db_path.write_text(content, encoding="utf-8")
print(f"Patched {count} table references with finvox. prefix")
