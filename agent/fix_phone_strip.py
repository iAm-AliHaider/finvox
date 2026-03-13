with open("agent.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    'caller_phone = metadata.get("phone", "")',
    'caller_phone = metadata.get("phone", "").strip()'
)

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Fixed: phone strip()")
