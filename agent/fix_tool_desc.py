with open("tools/caller.py", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace(
    'description="Create a new customer account after WhatsApp OTP verification. Requires the customer\'s full name and phone number. Optionally collect email, national ID (Iqama/Saudi ID), and city. ONLY use after OTP is verified."',
    'description="Create a new customer account. Requires full name and phone number. Optionally collect email, national ID (Iqama/Saudi ID), and city. No OTP needed for new accounts."'
)

with open("tools/caller.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Fixed tool description")
