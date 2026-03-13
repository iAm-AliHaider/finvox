"""Fix create_customer ID generation - handles C099 format IDs."""
with open("database.py", "r", encoding="utf-8") as f:
    code = f.read()

old = """        if row:
            num = int(row["id"].replace("CUST", "")) + 1
        else:
            num = 1
        new_id = f"CUST{num:03d}\""""

new = """        if row:
            import re as _re
            digits = _re.sub(r'[^0-9]', '', row['id'])
            num = int(digits) + 1 if digits else 1
        else:
            num = 1
        new_id = f"C{num:03d}\""""

if old in code:
    code = code.replace(old, new)
    with open("database.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("FIXED: create_customer now handles C099 format IDs")
else:
    print("ERROR: pattern not found")
