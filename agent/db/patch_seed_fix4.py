import pathlib
p = pathlib.Path(__file__).parent / "seed_ali.py"
s = p.read_text(encoding="utf-8")
# compliance_flags status: open|investigating|resolved|dismissed
s = s.replace("'medium','pending')", "'medium','open')")
s = s.replace("'high','pending')", "'high','investigating')")
p.write_text(s, encoding="utf-8")
print("Fixed compliance status")
