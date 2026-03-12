import pathlib
p = pathlib.Path(__file__).parent / "seed_ali.py"
src = p.read_text(encoding="utf-8")
src = src.replace("'upcoming'", "'due'")
p.write_text(src, encoding="utf-8")
print("Fixed: upcoming -> due")
