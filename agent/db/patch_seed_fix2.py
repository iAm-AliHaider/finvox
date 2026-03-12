import pathlib
p = pathlib.Path(__file__).parent / "seed_ali.py"
s = p.read_text(encoding="utf-8")
# Fix fund risk ratings (1-5 scale)
s = s.replace(",8,1.2,3.8,", ",4,1.2,3.8,")   # F001 equity 8->4
s = s.replace(",5,0.8,2.5,", ",3,0.8,2.5,")   # F002 balanced 5->3
s = s.replace(",1,0.3,0.9,", ",1,0.3,0.9,")   # F003 money_market stays 1
s = s.replace(",9,2.5,7.2,", ",5,2.5,7.2,")   # F004 tech equity 9->5
s = s.replace(",3,0.4,1.3,", ",2,0.4,1.3,")   # F005 sukuk 3->2
s = s.replace(",6,0.7,2.1,", ",4,0.7,2.1,")   # F006 RE 6->4
# Fix fund categories
s = s.replace("'fixed_income'", "'sukuk'")
s = s.replace("'balanced','SAR',108", "'hybrid','SAR',108")
# Fix portfolio risk scores too (1-5 scale? check if constrained)
# Actually portfolios risk_score is unconstrained integer, leave as-is
p.write_text(s, encoding="utf-8")
print("Fixed fund constraints")
