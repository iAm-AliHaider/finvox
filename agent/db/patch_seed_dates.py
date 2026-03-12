"""Fix seed_ali.py to cast date strings in SQL."""
import pathlib
p = pathlib.Path(__file__).parent / "seed_ali.py"
src = p.read_text(encoding="utf-8")

# Fix loan_payments INSERT to cast dates
old = '"""INSERT INTO finvox.loan_payments (id,loan_id,due_date,amount_due,amount_paid,paid_date,status)\n            VALUES ($1,$2,$3,$4,$5,$6,$7)"""'
new = '"""INSERT INTO finvox.loan_payments (id,loan_id,due_date,amount_due,amount_paid,paid_date,status)\n            VALUES ($1,$2,$3::date,$4,$5,$6::date,$7)"""'
src = src.replace(old, new)

# Add 'from datetime import date' if not there
if "from datetime import date" not in src:
    src = src.replace("import asyncio, sys", "import asyncio, sys\nfrom datetime import date")

p.write_text(src, encoding="utf-8")
print("Fixed date casting")
